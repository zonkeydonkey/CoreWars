#!/usr/bin/python
import pygame
from pygame.locals import *
import graphics
import serverSQL
import socket
import sys
import thread
import threading


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
		elif titles[index]=='Start':
		    filename = self._scenes_line[self._sceneID].get_filename()
		    self.load_file(filename)
	            #self.start_battle(core_size);
		elif titles[index]=='Scores':
	            self._sceneID+=1;
                    self.load_scene()
                    self.show_statistics(self._userID)
		elif titles[index]=='back':
	            self._sceneID-=1;
                    self.load_scene()
		elif titles[index]=='remove':
                    scene = self._scenes_line[self._sceneID]
                    self.db_remove_warrior(scene.get_convict())
                    text = self.db_get_warriors(self._userID)
	            scene.display_info(self._display_surf,text)
        if event.type == pygame.QUIT:
            self._running = False


    def on_loop(self):
        if self._reply!=self._old_reply:
            if self._reply.startswith('users:'):
                self._scenes_line[self._sceneID].save_users(self._display_surf,self._reply[6:])
            elif self._reply.startswith('error:'):
                self._scenes_line[self._sceneID].display_info(self._display_surf,'Error ocures, check console')
            elif self._reply.startswith('compiled:'):
                self._scenes_line[self._sceneID].display_info(self._display_surf,'Compilation completed!')
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
        """Send name of warrior to compiler and start program"""
	self.send(self._socket,'filename:'+filename)
        db_add_warrior(filename, self._userID)


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

    def db_add_warrior(self, filename, userID):
        sql = serverSQL.ServerSQL()
	cur = sql.connect()
        ID = sql.add_warrior(cur,filename,userID)
        sql.close_conn(cur)
        return ID
        

    def db_remove_warrior(self, convict):
        sql = serverSQL.ServerSQL()
        cur = sql.connect()
        warrior_id = sql.get_warrior_id(cur,convict)
        print 'Warrior:'+str(warrior_id)
        count = sql.remove_warrior(cur,warrior_id)
        sql.close_conn(cur)
        return count

    def db_get_warriors(self, userID):
        sql = serverSQL.ServerSQL()
        cur = sql.connect()
        rest = sql.get_warriors(cur,userID)
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
