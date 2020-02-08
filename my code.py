from djitellopy.tello import Tello
import cv2
import pygame
import numpy as np
import time

# Speed of the drone
S = 60
# Frames per second of the pygame window display
FPS = 25


class FrontEnd(object):
    """ Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counter clockwise and clockwise rotations
            - W and S: Up and down.
    """

    def __init__(self):
        # Init pygame
        pygame.init()

        # Creat pygame window
        pygame.display.set_caption("Tello video stream")

        # Center of screen - 480,360
        self.screen = pygame.display.set_mode([960, 720])
        

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(pygame.USEREVENT + 1, 50)

    def run(self):

        if not self.tello.connect():
            print("Tello not connected")
            return

        if not self.tello.set_speed(self.speed):
            print("Not set speed to lowest possible")
            return

        # In case streaming is on. This happens when we quit this program without the escape key.
        if not self.tello.streamoff():
            print("Could not stop video stream")
            return

        if not self.tello.streamon():
            print("Could not start video stream")
            return

        frame_read = self.tello.get_frame_read()

        should_stop = False
        while not should_stop:

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.update()
                elif event.type == pygame.QUIT:
                    should_stop = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                frame_read.stop()
                break

            self.screen.fill([0, 0, 0])
            frame = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)

            #------------FACIAL RECOGNITION-----------------------
            self.faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            self.gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            self.faces = self.faceCascade.detectMultiScale(
                self.gray,
                scaleFactor = 1.1,
                minNeighbors = 5,
                minSize = (30,30),
                flags = cv2.CASCADE_SCALE_IMAGE
                )
            #self.faces returns the faces it detects in a nested list [[face1],[face2]]
            #each list contains[x-axis,y-axis,width,height]
            #-----------------------------------------------------

            
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))

            #-----------------DRAW BOUNDINGBOX ON FACE------------
            self.colorofbox = pygame.Color(0,255,0)

            for item in self.faces:
                pygame.draw.rect(self.screen,self.colorofbox,pygame.Rect(item[0],item[1],item[2],item[3]),2)

            #-----------------------------------------------------

            pygame.display.update()

            #----CONTROL THE DRONE BASED ON THE BOUNDING BOX------

            if len(self.faces)>0:

                self.selectedface = self.faces[0]
                
                for item in self.faces:
                    if (item[2]*item[3])>(self.selectedface[2]*self.selectedface[3]):
                        self.selectedface = item
                
                
                self.centeredaxis = [self.selectedface[0]+(self.selectedface[2]//2),self.selectedface[1]+(self.selectedface[3]//2)]

                if self.centeredaxis[0] < 480:
                    print("left")
                    self.yawleft()
                    self.update()
                   
                elif self.centeredaxis[0] > 480:
                    print("right")
                    self.yawright()
                    self.update()
            else:
                self.emergencystop()
                self.update()
                  
            #-----------------------------------------------------
            

            time.sleep(1 / FPS)

        # Call it always before finishing. To deallocate resources.
        self.tello.end()

    def forward(self):
        self.for_back_velocity = S
        
    def backward(self):
        self.for_back_velocity = -S

    def left(self):
        self.left_right_velocity = -S

    def right(self):
        self.left_right_velocity = S

    def up(self):
        self.up_down_velocity = S

    def down(self):
        self.up_down_velocity = -S

    def yawleft(self):
        self.yaw_velocity = -S

    def yawright(self):
        self.yaw_velocity = S

    def takeoff(self):
        self.tello.takeoff()
        self.send_rc_control = True

    def land(self):
        self.tello.land()
        self.send_rc_control = False

    def emergencystop(self):
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
    
    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw counter clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                       self.yaw_velocity)


def main():
    frontend = FrontEnd()

    # run frontend
    frontend.run()


if __name__ == '__main__':
    main()
