//
// Created by Sylwia Blach on 4/26/17.
//

#ifndef REDCODEINTERPRETER_ZEROARGSINSTRUCTION_HPP
#define REDCODEINTERPRETER_ZEROARGSINSTRUCTION_HPP

#include "Instruction.hpp"

class ZeroArgsInstruction : public Instruction
{
public:
    ZeroArgsInstruction (RedcodeInterpreter::TokenType type) : Instruction(type)
    {}

};

typedef std::shared_ptr<ZeroArgsInstruction> ZeroArgsInstrPtr;

#endif //REDCODEINTERPRETER_ZEROARGSINSTRUCTION_HPP
