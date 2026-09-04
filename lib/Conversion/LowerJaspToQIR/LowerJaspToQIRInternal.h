#pragma once

#include <cstdint>
#include <memory>
#include <optional>

#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/StringRef.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Transforms/DialectConversion.h"

namespace mlir::jasp::internal {

enum class ResourceManagement {
    Static,
    Dynamic,
};

struct LowerJaspToQIROptions {
    ResourceManagement resourceManagement = ResourceManagement::Static;
    int64_t resultBufferSize = 64;

    bool isDynamic() const
    {
        return resourceManagement == ResourceManagement::Dynamic;
    }
};

struct QubitArrayInfo {
    int64_t base = 0;
    int64_t count = 0;
};

struct MeasurementResultRange {
    int64_t base = 0;
    int64_t count = 0;
};

struct QIRModuleFeatures {
    bool hasIrFunctions = false;
    bool hasBackwardsBranching = false;
    bool hasMultipleTargetBranching = false;
    bool hasMultipleReturnPoints = false;
    bool hasFloatComputations = false;
};

/// Facts established before dialect conversion and consumed by lowering
/// patterns or by the final QIR module annotation step.
struct LowerJaspToQIRModuleInfo {
    int64_t requiredQubits = 0;
    int64_t requiredResults = 0;
    QIRModuleFeatures features;

    llvm::DenseMap<Operation *, QubitArrayInfo> qubitAllocations;
    llvm::DenseMap<Value, int64_t> qubitArraySizes;
    llvm::DenseMap<Operation *, MeasurementResultRange> measurementResultRanges;

    const QubitArrayInfo *getQubitAllocation(Operation *operation) const
    {
        auto iterator = qubitAllocations.find(operation);
        return iterator == qubitAllocations.end() ? nullptr : &iterator->second;
    }

    const MeasurementResultRange *
    getMeasurementResultRange(Operation *operation) const
    {
        auto iterator = measurementResultRanges.find(operation);
        return iterator == measurementResultRanges.end() ? nullptr
                                                         : &iterator->second;
    }
};

std::optional<ResourceManagement>
parseResourceManagement(llvm::StringRef value);
llvm::StringRef
stringifyResourceManagement(ResourceManagement resourceManagement);

FailureOr<LowerJaspToQIRModuleInfo>
prepareLowerJaspToQIRModule(ModuleOp module, const LowerJaspToQIROptions &options);

std::unique_ptr<TypeConverter>
createLowerJaspToQIRTypeConverter(MLIRContext &context,
                             const LowerJaspToQIROptions &options);

bool isSupportedQuantumGate(llvm::StringRef name);

void populateQubitManagementPatterns(TypeConverter &converter,
                                     RewritePatternSet &patterns,
                                     const LowerJaspToQIROptions &options,
                                     const LowerJaspToQIRModuleInfo &moduleInfo);

void populateQubitArrayOperationPatterns(TypeConverter &converter,
                                         RewritePatternSet &patterns,
                                         const LowerJaspToQIROptions &options);

void populateQuantumGatePatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns);

void populateMeasurementPatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns,
                                 const LowerJaspToQIROptions &options,
                                 const LowerJaspToQIRModuleInfo &moduleInfo);

void populateResetPatterns(TypeConverter &converter,
                           RewritePatternSet &patterns,
                           const LowerJaspToQIROptions &options);

void populateScalarizationPatterns(TypeConverter &converter,
                                   RewritePatternSet &patterns);

} // namespace mlir::jasp::internal
