//
// Created by Sylwia Blach on 4/26/17.
//

#ifndef REDCODEINTERPRETER_TWOARGSINSTRUCTION_HPP
#define REDCODEINTERPRETER_TWOARGSINSTRUCTION_HPP

#include <tuple>
#include "Instruction.hpp"
#include "../AddressingMode.hpp"
#include "../identifier/Identifier.hpp"
#include "../Modifier.hpp"

class TwoArgsInstruction : public Instruction
{
public:
    TwoArgsInstruction (std::string name, bool canModifiers) : canModifiers_(canModifiers)
    {
        Instruction(name);
    }

private:
    std::tuple<AddrModePtr, IdentifierPtr, ModifierPtr> aArg;
    std::tuple<AddrModePtr, IdentifierPtr, ModifierPtr> bArg;

    bool canModifiers_;
};

typedef std::shared_ptr<TwoArgsInstruction> TwoArgsInstrPtr;

#endif //REDCODEINTERPRETER_TWOARGSINSTRUCTION_HPP