import pygame, sys, random, math

pygame.init()

screen_size = 900,900
map_size_x = 2000
map_size_y = 2000
drag = 0.01
global_timer = 0
players_remaining = 30

camera_x = 0
camera_y = 0

movement_none = -1
movement_forward = 0
movement_forward_left = 1
movement_left = 2
movement_back_left = 3
movement_back = 4
movement_back_right = 5
movement_right = 6
movement_forward_right = 7

screen = pygame.display.set_mode(screen_size)
screen.fill(255)

vision_screen = pygame.Surface((map_size_x,map_size_y))
vision_screen_pxarray = pygame.PixelArray(vision_screen)
vision_screen_pxarray[:] = (255,255,255)

def rotate_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

def angle(vector):
    ang = 0
    if vector[0] >= 0 and vector[1] < 0:
        ang = math.atan(vector[0]/-vector[1])
    if vector[0] > 0 and vector[1] >= 0:
        ang = math.atan(-vector[1]/-vector[0])+math.radians(90)
    if vector[0] <= 0 and vector[1] > 0:
        ang = math.atan(vector[0]/-vector[1])+math.radians(180)
    if vector[0] < 0 and vector[1] <= 0:
        ang = math.atan(-vector[1]/-vector[0])+math.radians(270)
    return ang

class Bullet:
    def __init__(self,x,y,ang,player):
        self.x = x
        self.y = y
        self.ang = ang
        self.spd = 3
        self.player = player
        self.lifetime = 250
        self.collision_box = pygame.Rect(x+2,y+2,6,6)
        self.collided = False
        self.base_image = pygame.Surface((10,10),flags=pygame.SRCALPHA)
        self.base_image.fill((255,255,255,0))
        pygame.draw.circle(self.base_image,(0,0,0),(5,5),5)
        pygame.draw.line(self.base_image,(255,0,0),(5,0),(5,5),1)
        self.image = self.base_image
        self.image = rotate_center(self.image,math.degrees(self.ang))
    
    def update(self):
        try:
            pixel_below = vision_screen_pxarray[round(self.x+5),round(self.y+5)]
            if self.x > 0 and self.x < map_size_x and self.y > 0 and self.y < map_size_y and\
            pixel_below != vision_screen.map_rgb(255,255,255) and pixel_below != self.player:
                self.collided = True
                try:
                    players[pixel_below].hp -= 1
                except:
                    pass
        except:
            self.collided = True
        
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.collided = True

        self.x += math.cos(self.ang+0.5*math.pi)*self.spd
        self.y += -math.sin(self.ang+0.5*math.pi)*self.spd

        self.image = self.base_image
        self.image = rotate_center(self.image,math.degrees(self.ang))

class Eye:
    def __init__(self,x,y,ang_offset,player):
        self.x = x
        self.y = y
        self.ang_offset = ang_offset
        self.ang = ang_offset
        self.player = player
        self.vision_jump = 7
        self.seen = None
    
    def see(self):
        see_point_x = self.x
        see_point_y = self.y
        jump_x = math.cos(self.ang+0.5*math.pi)*self.vision_jump
        jump_y = -math.sin(self.ang+0.5*math.pi)*self.vision_jump
        for i in range(40):
            see_point_x += jump_x
            see_point_y += jump_y
            try:
                pixel_below = vision_screen_pxarray[round(see_point_x),round(see_point_y)]
            except:
                self.seen = None
                return
            if pixel_below != vision_screen.map_rgb(255,255,255) and pixel_below != self.player:
                self.seen = pixel_below
                pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))
                return
        self.seen = None
        pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))

class Player:
    def __init__(self,x,y,id):
        self.x = x
        self.y = y
        self.ang = random.random()*math.pi*2
        self.id = id
        self.spd = 0
        self.shoot_cooldown = 0
        self.movement_direction = movement_none
        self.ang_change = 0
        self.hp = 10
        self.death_position = 0

        self.eyes = []
        self.eyes.append(Eye(self.x+15,self.y+15,0,self.id))
        eye_number = 10
        for i in range(eye_number):
            self.eyes.append(Eye(self.x+15,self.y+15,-math.pi*0.25+i*math.pi*(1/(eye_number*2)),self.id))

        self.hidden_nodes = []
        for i in range(15):
            self.hidden_nodes.append(0)

        self.outputs = []
        for i in range(11):
            self.outputs.append(0)

        self.weights_1 = []
        for i in range(eye_number+1):
            self.weights_1.append([])
            for j in range(len(self.hidden_nodes)):
                self.weights_1[i].append(-1+(random.random()*2))
        self.weights_2 = []
        for i in range(len(self.hidden_nodes)):
            self.weights_2.append([])
            for j in range(11):
                self.weights_2[i].append(-1+(random.random()*2))

        self.base_image = pygame.Surface((30,30),flags=pygame.SRCALPHA)
        self.base_image.fill((255,255,255,0))
        pygame.draw.circle(self.base_image,(0,0,0),(15,15),10,3)
        pygame.draw.circle(self.base_image,(180,180,180),(10,6),4)
        pygame.draw.circle(self.base_image,(255,0,0),(10,4),2)
        pygame.draw.circle(self.base_image,(180,180,180),(20,6),4)
        pygame.draw.circle(self.base_image,(255,0,0),(20,4),2)
        self.image = self.base_image
        self.image = rotate_center(self.image,math.degrees(self.ang))

    def __repr__(self):
        return str((self.x,self.y))
        
    def ai(self):
        inputs = []

        for eye in self.eyes:
            if eye.seen != None: 
                inputs.append(1)
            else:
                inputs.append(-1)

        for i,inp in enumerate(inputs):
            for j,hid in enumerate(self.hidden_nodes):
                self.hidden_nodes[j] = inp*self.weights_1[i][j]

        for i,hid in enumerate(self.hidden_nodes):
            for j,out in enumerate(self.outputs):
                self.outputs[j] = hid*self.weights_2[i][j]

        print(self.outputs)

    def see(self):
        for eye in self.eyes:
            eye.player = self.id
            eye.ang = eye.ang_offset+self.ang
            eye.see()

    def shoot(self):
        bullets.append(Bullet(self.x+math.cos(self.ang+0.5*math.pi)*20+12,
        self.y-math.sin(self.ang+0.5*math.pi)*20+12,
        self.ang,
        self.id))

    def update(self):
        self.see()

        self.ai()

        if self.ang > 2*math.pi:
            self.ang -= 2*math.pi
        if self.ang < 0:
            self.ang += 2*math.pi

        if global_timer % 100 == 0:
            self.shoot()

        self.ang += self.ang_change

        vision_screen_pxarray[self.x+4:self.x+26,self.y+4:self.y+26] = (255,255,255)

        if self.movement_direction == movement_forward:
            self.x += math.cos(self.ang+0.5*math.pi)*self.spd
            self.y += -math.sin(self.ang+0.5*math.pi)*self.spd
        elif self.movement_direction == movement_forward_left:
            self.x += math.cos(self.ang+0.75*math.pi)*self.spd
            self.y += -math.sin(self.ang+0.75*math.pi)*self.spd
        elif self.movement_direction == movement_left:
            self.x += math.cos(self.ang+math.pi)*self.spd
            self.y += -math.sin(self.ang+math.pi)*self.spd
        elif self.movement_direction == movement_back_left:
            self.x += math.cos(self.ang+1.25*math.pi)*self.spd
            self.y += -math.sin(self.ang+1.25*math.pi)*self.spd
        elif self.movement_direction == movement_back:
            self.x += math.cos(self.ang+1.5*math.pi)*self.spd
            self.y += -math.sin(self.ang+1.5*math.pi)*self.spd
        elif self.movement_direction == movement_back_right:
            self.x += math.cos(self.ang+1.75*math.pi)*self.spd
            self.y += -math.sin(self.ang+1.75*math.pi)*self.spd
        elif self.movement_direction == movement_right:
            self.x += math.cos(self.ang)*self.spd
            self.y += -math.sin(self.ang)*self.spd
        elif self.movement_direction == movement_forward_right:
            self.x += math.cos(self.ang+0.25*math.pi)*self.spd
            self.y += -math.sin(self.ang+0.25*math.pi)*self.spd

        if self.hp > 0:
            vision_screen_pxarray[self.x+4:self.x+26,self.y+4:self.y+26] = (0,0,self.id)

        self.image = self.base_image
        self.image = rotate_center(self.image,math.degrees(self.ang))

        self.shoot_cooldown -= 1

players = []
bullets = []

for i in range(30):
    players.append(Player(random.randrange(map_size_x),random.randrange(map_size_y),i))

living_players = players

pygame.display.flip()

while global_timer < 5:
    screen.fill((255,255,255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    key = pygame.key.get_pressed()
    if key[pygame.K_LEFT]: 
        camera_x -= 4
    if key[pygame.K_RIGHT]:
        camera_x += 4
    if key[pygame.K_UP]:
        camera_y -= 4
    if key[pygame.K_DOWN]:
        camera_y += 4

    for i,player in enumerate(players):
        player.id = i
        if player.death_position == 0:
            if player.hp <= 0:
                player.death_position = players_remaining
                players_remaining -= 1
            player.update()
            screen.blit(player.image,(player.x-camera_x,player.y-camera_y))
    
    for player in reversed(living_players):
        if player.death_position != 0:
            living_players.remove(player)

    for bullet in reversed(bullets):
        bullet.update()
        screen.blit(bullet.image,(bullet.x-camera_x,bullet.y-camera_y))
        if bullet.collided:
            bullets.remove(bullet)

    pygame.display.flip()
    
    global_timer += 1