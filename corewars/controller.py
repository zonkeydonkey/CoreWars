#!/usr/bin/python
import pygame
from pygame.locals import *
import graphics
import serverSQL
import socket
import sys
import thread
import threading

#TODO:
#      - rozpoczecie rozgrywki, obsluga przyciskow (start)
#      - dodatki, bajery, w stylu: status bitwy (jakie info moge dostac od Sylwii?)
#      - czy ja mam polaczyc dwa programy w jeden?
#      - eksport klas Sylwii do pythona, wykorzystanie w remote (errorLoger, co jeszcze?)
#      - testy (czy nalezy testowac baze danych? polaczenie z serwerem? grafike? co powinno byc przetestowane)
#      - dokumentacja (oxygen)


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.weight, self.height = 700, 500
	self._tab_counter = False
	self._scenes_line = [
		graphics.Logger(),
		graphics.Game(),
                graphics.Statistics()
	]
        self._userID = 0;
	self._sceneID = 0;
        self._connected = False;
        self._old_reply = []
        self._reply = []
	self._socket = self.create_socket()
	#thread.start_new_thread (self.connect, (self._socket,))
        #self.connect(self._socket)
        #thread.start_new_thread (self.listen, (self._socket,))
        

    def load_scene(self):
	self._scenes_line[self._sceneID].on_init(self._display_surf)
        #self._scenes_line[self._sceneID].light_up(self._display_surf, self._scenes_line[self._sceneID]._boxes[0])
 
    def on_init(self):
        self.connect(self._socket)
        thread.start_new_thread (self.listen, (self._socket,))
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption('CoreWars')
        self.load_scene()
        self._running = True

 
    def on_event(self, event):
	"""Handling events """
        if event.type == KEYDOWN:
            if event.key == K_TAB:
                self._tab_counter= not self._tab_counter
	        if not self._tab_counter:
	            box = self._scenes_line[self._sceneID]._boxes[0]
                else:
                    box = self._scenes_line[self._sceneID]._boxes[1]
                self._scenes_line[self._sceneID].light_up(self._display_surf, box)
            elif event.key == K_RETURN:
		pass
            else:
		self._scenes_line[self._sceneID].add_sign(self._display_surf,event.key,self._tab_counter)
            #print chr(event.key)
	elif event.type == MOUSEBUTTONDOWN:
	    pos = pygame.mouse.get_pos()
            print pos
	    sprites = self._scenes_line[self._sceneID]._sprites[0]
	    titles = self._scenes_line[self._sceneID]._sprites[1]
	    clicked_sprites = [s for s in sprites if s.collidepoint(pos)]
	    print clicked_sprites
	    if clicked_sprites:
                index = sprites.index(clicked_sprites[0])
                if titles[index]=='Sign in':
                    self.sign_in()
		elif titles[index]=='Sign up':
		    self.sign_up()
		elif titles[index]=='Load':
		    filename = self._scenes_line[self._sceneID].get_filename()
		    self.load_file(filename)
		elif titles[index]=='Start':
                    core_size = self._scenes_line[self._sceneID]._core_size_str
                    if not core_size:
                        core_size = self._scenes_line[self._sceneID]._core_size
	            self.start_battle(core_size);
		elif titles[index]=='Scores':
	            self._sceneID+=1;
                    self.load_scene()
                    self.show_statistics(self._userID)
		elif titles[index]=='back':
	            self._sceneID-=1;
                    self.load_scene()
		elif titles[index]=='remove':
                    scene = self._scenes_line[self._sceneID]
                    text = self.db_remove_warrior(scene.get_convict())
	            scene.display_info(self._display_surf,text)
        if event.type == pygame.QUIT:
            self._running = False


    def on_loop(self):
        if self._reply!=self._old_reply:
            if self._reply.startswith('users:'):
                self._scenes_line[self._sceneID].save_users(self._display_surf,self._reply[6:])
            elif self._reply.startswith('compiler:'):
                self._scenes_line[self._sceneID].display_info(self._display_surf,self._reply[9:])
            self._old_reply = self._reply
        #pass


    def on_render(self):
        pygame.display.flip()

    def on_cleanup(self):
        if self._connected:
	    self.close(self._socket)
        pygame.quit()

    def on_execute(self):
        """Main loop"""
        if self.on_init() == False or not self._connected:
            self._running = False
        while( self._running ):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()


    def load_file(self,filename):
        """Send name of warrior program to compiler"""
	self.send(self._socket,'filename:'+filename)
        sql = serverSQL.ServerSQL()
	cur = sql.connect()
        if sql.add_warrior(cur,filename,self._userID): #name already in use
            self._scenes_line[self._sceneID].display_info(self._display_surf,'Username already exist.')
        else:
            self._scenes_line[self._sceneID].display_info(self._display_surf,"Loaded file: "+filename)
        sql.close_conn(cur)


    def sign_in(self):
	"""Connect to SQL server, check user""" 
	usr = self._scenes_line[self._sceneID].get_login()
	psw = self._scenes_line[self._sceneID].get_password()
        if not usr or not psw:
            return
        userID = self.db_auth(usr,psw)
	if userID: # if username and password is correct
	    self._sceneID+=1;
            self.send(self._socket,usr)
	else: # display error
	    self._scenes_line[self._sceneID].display_info(self._display_surf,"Incorrect login or password.")
        self.load_scene()
        self._userID = userID
        self._tab_counter= not self._tab_counter


    def sign_up(self):
        """Create new account"""
	usr = self._scenes_line[self._sceneID].get_login()
	psw = self._scenes_line[self._sceneID].get_password()
        if not usr or not psw:
            return
        if self.db_add_usr(usr,psw): #name already in use
            self._scenes_line[self._sceneID].display_info(self._display_surf,'Username already exist.')
        else:
	    self._scenes_line[self._sceneID].display_info(self._display_surf,'Account created. Please, sing in.')
	self._scenes_line[self._sceneID].on_init(self._display_surf)
        self._tab_counter= not self._tab_counter


    def start_battle(self, core_size):
        """..."""
        self.send(self._socket,'start:'+str(core_size))


    def show_statistics(self, userID):
        """ Show scores in statistics scene """
        scene = self._scenes_line[self._sceneID]
    	sql = serverSQL.ServerSQL()
	cur = sql.connect()
        text = sql.get_warriors(cur,userID)
	scene.display_info(self._display_surf,text)
        text = sql.get_statistics(cur)
	scene.display_info(self._display_surf,text,1)
        sql.close_conn(cur)



    def db_auth(self,login,password):
        """ Authentication in database """
    	sql = serverSQL.ServerSQL()
	cur = sql.connect()
	userID = sql.get_user_id(cur,login,password)
        sql.close_conn(cur)
        return userID

    def db_add_usr(self,login,password):
        """ Save new user in database """
    	sql = serverSQL.ServerSQL()
	cur = sql.connect()
        userID = sql.add_user(cur,login,password)
        sql.close_conn(cur)
        return userID

    def db_remove_warrior(self, convict):
        sql = serverSQL.ServerSQL()
        cur = sql.connect()
        warrior_id = sql.get_warrior_id(cur,convict)
        sql.remove_warrior(cur,warrior_id)
        rest = sql.get_warriors(cur,self._userID)
        sql.close_conn(cur)
        return rest


    def create_socket(self):
	"""Create an INET, STREAMing socket"""
	try:
    	    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error:
    	    print 'Failed to create socket'
    	    sys.exit()
	print 'Socket Created'
	return self._socket

    def connect(self,s):
	"""Connect to remote server"""
        try:
	    s.connect(('localhost', 4000))
        except socket.error as msg:
            print 'Connection failed: ' + msg[1]
            print 'Cannot connect to remote server. Please, check if server is running.'
            sys.exit()
	print 'Socket Connected '
        self._connected = True
        #thread.start_new_thread (self.listen, (self._socket,))


    def send(self,s,message):
	"""Send some data to remote server"""
	try :
    	    s.sendall(message)
	except socket.error:
    	    print 'Send failed'
    	    sys.exit()
	print 'Message send successfully'

    def recive_data(self,s):
	"""Receive data from server"""
	self._reply = s.recv(4096)
	print self._reply
	return self._reply

    def close(self,s):
        """Close connection with remote server"""
        if self._connected:
	    self.send(self._socket,'bye')
	    s.close()
	    print 'Connection with server closed'

    def listen(self,s):
        """ Start listening to remote server """
        while(self._running):
            self.recive_data(s)
        

if __name__ == "__main__" :
    theApp = App()
    theApp.on_execute()

