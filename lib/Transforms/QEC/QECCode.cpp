#include "QECCode.h"

#include "llvm/ADT/StringSwitch.h"

namespace jasp_to_qir::qec {

std::unique_ptr<Code> createDummyCode();

std::unique_ptr<Code> createCode(llvm::StringRef name)
{
    using Factory = std::unique_ptr<Code> (*)();
    auto factory = llvm::StringSwitch<Factory>(name)
                       .Case("dummy", createDummyCode)
                       .Default(nullptr);
    return factory ? factory() : nullptr;
}

} // namespace jasp_to_qir::qec
