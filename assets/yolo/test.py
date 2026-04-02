import cv2
import numpy as np
import onnxruntime as ort

# -----------------------------
# 配置best.onnx
ONNX_MODEL = r"best.onnx"          # 你的 YOLOv10 导出的 ONNX 模型
IMAGE_PATH = r"D:\PyProject\yolov10-main\data\shubiao\images\150.bmp"  # 改成jpg可以检测到
#IMAGE_PATH = r"D:\PyProject\yolov10-main\datasets\assets\30.jpg"   #训练原图，可以找到
INPUT_SIZE = 640                   # YOLO 输入尺寸
CONF_THRESH = 0.03                 # 置信度阈值，可调低
IOU_THRESH = 0.5                   # NMS 阈值
# -----------------------------

# 初始化 ONNX Runtime
providers = ['CPUExecutionProvider']  # 如果有 GPU，可改成 ['CUDAExecutionProvider','CPUExecutionProvider']
session = ort.InferenceSession(ONNX_MODEL, providers=providers)
input_name = session.get_inputs()[0].name

# NMS 函数
def nms(boxes, scores, iou_threshold=0.5):
    x1 = boxes[:,0]
    y1 = boxes[:,1]
    x2 = boxes[:,2]
    y2 = boxes[:,3]
    areas = (x2-x1)*(y2-y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2-xx1)
        h = np.maximum(0.0, yy2-yy1)
        inter = w*h
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    return keep

# 读取图片
frame = cv2.imread(IMAGE_PATH)
if frame is None:
    raise RuntimeError("无法打开图片")

h, w = frame.shape[:2]

# 预处理
img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = img.transpose(2,0,1)[np.newaxis, ...].astype(np.float32)/255.0

# ONNX 推理
outputs = session.run(None, {input_name: img})
pred = outputs[0][0]  # [N,6]

boxes = pred[:, :4]
scores = pred[:, 4]
classes = pred[:, 5]

# 缩放回原图
scale_x = w / INPUT_SIZE
scale_y = h / INPUT_SIZE
boxes[:, [0,2]] *= scale_x
boxes[:, [1,3]] *= scale_y

# 置信度过滤
mask = scores > CONF_THRESH
boxes, scores, classes = boxes[mask], scores[mask], classes[mask]

# NMS
keep = nms(boxes, scores, IOU_THRESH)
boxes, scores, classes = boxes[keep], scores[keep], classes[keep]

# 打印检测结果
print(f"检测到 {len(boxes)} 个目标：")
for i in range(len(boxes)):
    print(f"类 {int(classes[i])}, 置信度 {scores[i]:.3f}, 坐标 {boxes[i]}")

# 可视化
for i in range(len(boxes)):
    x1, y1, x2, y2 = boxes[i].astype(int)
    conf = scores[i]
    cls = int(classes[i])
    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
    cv2.putText(frame, f"{cls}:{conf:.2f}", (x1, y1-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

cv2.imshow("YOLO Debug", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()


