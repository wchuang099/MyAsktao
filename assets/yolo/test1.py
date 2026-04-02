import onnx
print(onnx.load("best.onnx").opset_import)
