import cv2
import mediapipe as mp
import pyautogui
import math

cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()

# Landmark indices (FaceMesh 468+10 layout)
NOSE_TIP = 1              # nose tip for cursor [web:14][web:20]
LEFT_EYE_UP = 159         # upper eyelid (left eye) [web:21][web:27]
LEFT_EYE_DOWN = 145       # lower eyelid (left eye) [web:21][web:27]
RIGHT_EYE_UP = 386        # upper eyelid (right eye) [web:21]
RIGHT_EYE_DOWN = 374      # lower eyelid (right eye) [web:21]

# Blink thresholds (tune for your face / camera)
BLINK_THRESHOLD = 0.004
BLINK_COOLDOWN_FRAMES = 10

left_cooldown = 0
right_cooldown = 0

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)
    landmark_points = output.multi_face_landmarks
    frame_h, frame_w, _ = frame.shape

    if landmark_points:
        landmarks = landmark_points[0].landmark

        # 1) Nose controls mouse cursor
        nose = landmarks[NOSE_TIP]
        nose_x = int(nose.x * frame_w)
        nose_y = int(nose.y * frame_h)
        cv2.circle(frame, (nose_x, nose_y), 4, (0, 255, 0), -1)

        screen_x = screen_w * nose.x
        screen_y = screen_h * nose.y
        pyautogui.moveTo(screen_x, screen_y)

        # 2) Left eye blink -> LEFT click
        left_up = landmarks[LEFT_EYE_UP]
        left_down = landmarks[LEFT_EYE_DOWN]
        lu = int(left_up.x * frame_w), int(left_up.y * frame_h)
        ld = int(left_down.x * frame_w), int(left_down.y * frame_h)
        cv2.circle(frame, lu, 3, (0, 255, 255), -1)
        cv2.circle(frame, ld, 3, (0, 255, 255), -1)

        left_dist = abs(left_up.y - left_down.y)

        # 3) Right eye blink -> RIGHT click
        right_up = landmarks[RIGHT_EYE_UP]
        right_down = landmarks[RIGHT_EYE_DOWN]
        ru = int(right_up.x * frame_w), int(right_up.y * frame_h)
        rd = int(right_down.x * frame_w), int(right_down.y * frame_h)
        cv2.circle(frame, ru, 3, (255, 255, 0), -1)
        cv2.circle(frame, rd, 3, (255, 255, 0), -1)

        right_dist = abs(right_up.y - right_down.y)

        # Cooldown counters to avoid multiple clicks per blink
        if left_cooldown > 0:
            left_cooldown -= 1
        if right_cooldown > 0:
            right_cooldown -= 1

        # Left blink -> left click
        if left_dist < BLINK_THRESHOLD and left_cooldown == 0:
            pyautogui.click(button="left")
            left_cooldown = BLINK_COOLDOWN_FRAMES

        # Right blink -> right click
        if right_dist < BLINK_THRESHOLD and right_cooldown == 0:
            pyautogui.click(button="right")
            right_cooldown = BLINK_COOLDOWN_FRAMES

    cv2.imshow('Nose + Blink Mouse', frame)
    if cv2.waitKey(1) & 0xFF == 27:   # ESC to quit
        break

cam.release()
cv2.destroyAllWindows()
