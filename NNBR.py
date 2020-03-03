import pygame, sys, random, math, time

pygame.init()

screen_size = 1800,1000
map_size_x = 2000
map_size_y = 2000
drag = 0.01
global_timer = 0
players_start = 30
players_remaining = players_start
death_tick = 500

generation = 0

clock = pygame.time.Clock()

fps = 30

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

class Bullet:
    def __init__(self,x,y,ang,player):
        self.x = x
        self.y = y
        self.ang = ang
        self.spd = 20
        self.player = player
        self.lifetime = 20
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
                    if players[pixel_below].hp > 0:
                        players[pixel_below].hp -= 1
                        players[pixel_below].last_hurt_by = self.player
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
        self.vision_jump = 10
        self.seen = -2
    
    def see(self):
        see_point_x = self.x
        see_point_y = self.y
        jump_x = math.cos(self.ang+0.5*math.pi)*self.vision_jump
        jump_y = -math.sin(self.ang+0.5*math.pi)*self.vision_jump
        for i in range(30):
            see_point_x += jump_x
            see_point_y += jump_y
            if i < 15:
                self.vision_jump = 15
            else:
                self.vision_jump = 25
            if see_point_x < 0 or see_point_y < 0:
                pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))
                self.seen = -1
                return
            try:
                pixel_below = vision_screen_pxarray[round(see_point_x),round(see_point_y)]
            except:
                pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))
                self.seen = -1
                return
            if pixel_below != vision_screen.map_rgb(255,255,255) and pixel_below != self.player:
                self.seen = pixel_below
                pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))
                return
        self.seen = -2
        pygame.draw.line(screen,0,(self.x-camera_x,self.y-camera_y),(see_point_x-camera_x,see_point_y-camera_y))

class Player:
    def __init__(self,x,y,id):
        self.x = x
        self.y = y
        self.ang = random.random()*math.pi*2
        self.id = id
        self.spd = 3
        self.shoot_cooldown = 0
        self.movement_direction = movement_none
        self.ang_change = 0
        self.hp = 5
        self.death_position = 0
        self.kills = 0
        self.last_hurt_by = None

        self.hp_loss_on_attack = 0

        self.eyes = []
        eye_number = 25
        for i in range(eye_number):
            self.eyes.append(Eye(self.x+15,self.y+15,-math.pi*0.25+i*math.pi*(1/(eye_number*2)),self.id))

        self.move_threshold = 3.5

        self.hidden_nodes = []
        for i in range(30):
            self.hidden_nodes.append(0)

        self.outputs = []
        for i in range(7):
            self.outputs.append(0)

        self.weights_1 = []
        for i in range(eye_number+4):
            self.weights_1.append([])
            for j in range(len(self.hidden_nodes)):
                self.weights_1[i].append(-1+(random.random()*2))
        self.weights_2 = []
        for i in range(len(self.hidden_nodes)):
            self.weights_2.append([])
            for j in range(len(self.outputs)):
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
            if eye.seen == -2: 
                inputs.append(-1)
            elif eye.seen == -1:
                inputs.append(0)
            else:
                inputs.append(1)

        self.hidden_nodes = []
        for i in range(30):
            self.hidden_nodes.append(0)

        for i in range(3):
            inputs.append(min(max(self.outputs[4+i],-1),1))

        self.outputs = []
        for i in range(7):
            self.outputs.append(0)

        inputs.append(1)

        for i,inp in enumerate(inputs):
            for j,hid in enumerate(self.hidden_nodes):
                self.hidden_nodes[j] += inp*self.weights_1[i][j]

        for i,hid in enumerate(self.hidden_nodes):
            for j,out in enumerate(self.outputs):
                self.outputs[j] += hid*self.weights_2[i][j]

        if self.outputs[0] <= -self.move_threshold and self.outputs[1] <= -self.move_threshold:
            self.movement_direction = movement_back_left
        if self.outputs[0] <= -self.move_threshold and self.outputs[1] > -self.move_threshold and self.outputs[1] < self.move_threshold:
            self.movement_direction = movement_left
        if self.outputs[0] <= -self.move_threshold and self.outputs[1] >= self.move_threshold:
            self.movement_direction = movement_forward_left
        if self.outputs[0] > -self.move_threshold and self.outputs[0] < self.move_threshold and self.outputs[1] <= -self.move_threshold:
            self.movement_direction = movement_back
        if self.outputs[0] > -self.move_threshold and self.outputs[0] < self.move_threshold and self.outputs[1] > -self.move_threshold and self.outputs[1] < self.move_threshold:
            self.movement_direction = movement_none
        if self.outputs[0] > -self.move_threshold and self.outputs[0] < self.move_threshold and self.outputs[1] >= self.move_threshold:
            self.movement_direction = movement_forward
        if self.outputs[0] >= self.move_threshold and self.outputs[1] <= -self.move_threshold:
            self.movement_direction = movement_back_right
        if self.outputs[0] >= self.move_threshold and self.outputs[1] > -self.move_threshold and self.outputs[1] < self.move_threshold:
            self.movement_direction = movement_right
        if self.outputs[0] >= self.move_threshold and self.outputs[1] >= self.move_threshold:
            self.movement_direction = movement_forward_right
        
        if self.outputs[2] <= -self.move_threshold:
            self.ang -= 0.05
        if self.outputs[2] >= self.move_threshold:
            self.ang += 0.05
        
        if self.outputs[3] >= self.move_threshold:
            self.spd = 3
            if self.shoot_cooldown <= 0:
                self.shoot()
                self.shoot_cooldown = 15
        else:
            self.spd = 5

    def see(self):
        for eye in self.eyes:
            eye.player = self.id
            eye.x = self.x+15
            eye.y = self.y+15
            eye.ang = eye.ang_offset+self.ang
            eye.see()

    def shoot(self):
        bullets.append(Bullet(self.x+math.cos(self.ang+0.5*math.pi)+12,
        self.y-math.sin(self.ang+0.5*math.pi)+12,
        self.ang,
        self.id))
        self.hp -= self.hp_loss_on_attack

    def update(self):
        self.see()

        self.ai()

        if self.ang > 2*math.pi:
            self.ang -= 2*math.pi
        if self.ang < 0:
            self.ang += 2*math.pi

        vision_screen_pxarray[round(self.x-4):round(self.x+34),round(self.y-4):round(self.y+34)] = (255,255,255)

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

        if self.x < 100:
            self.x = 100
        if self.x > map_size_x-100:
            self.x = map_size_x-100
        if self.y < 100:
            self.y = 100
        if self.y > map_size_y-100:
            self.y = map_size_y-100

        if self.hp > 0:
            vision_screen_pxarray[round(self.x-4):round(self.x+34),round(self.y-4):round(self.y+34)] = (0,0,self.id)

        self.image = self.base_image
        self.image = rotate_center(self.image,math.degrees(self.ang))

        self.shoot_cooldown -= 1

players = []
bullets = []

print("Generation 0")

for i in range(players_start):
    players.append(Player(random.randrange(100,map_size_x-100),random.randrange(100,map_size_y-100),i))

pygame.display.flip()

while True:
    clock.tick(fps)

    screen.fill((255,255,255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    key = pygame.key.get_pressed()
    if key[pygame.K_LEFT]: 
        camera_x -= 12
    if key[pygame.K_RIGHT]:
        camera_x += 12
    if key[pygame.K_UP]:
        camera_y -= 12
    if key[pygame.K_DOWN]:
        camera_y += 12

    for i,player in enumerate(players):
        player.id = i
        if global_timer % death_tick == 0:
            player.hp -= 1
            player.last_hurt_by = None
        if player.death_position == 0:
            if player.hp <= 0:
                player.death_position = players_remaining
                players_remaining -= 1
                if player.last_hurt_by != None:
                    killer = players[player.last_hurt_by]
                    try:
                        killer.kills += 1
                        killer.health += 5
                    except:
                        players[random.randrange(len(players)-1)].kills += 1
                else:
                    players[random.randrange(len(players)-1)].kills += 1
            #try:
            player.update()
            #except:
            #    print("Player Update Error")
            screen.blit(player.image,(player.x-camera_x,player.y-camera_y))

    for bullet in reversed(bullets):
        bullet.update()
        screen.blit(bullet.image,(bullet.x-camera_x,bullet.y-camera_y))
        if bullet.collided:
            bullets.remove(bullet)

    if players_remaining <= 1:
        new_players = []
        for player in players:
            if player.kills > 0:
                for i in range(player.kills):
                    new_player = Player(random.randrange(100,map_size_x-100),random.randrange(100,map_size_y-100),0)
                    new_player.weights_1 = player.weights_1
                    new_player.weights_2 = player.weights_2

                    for j in range(len(new_player.weights_1)):
                        for k in range(len(new_player.weights_1[j])):
                            new_player.weights_1[j][k] += -0.15+random.random()*0.3

                    for j in range(len(new_player.weights_2)):
                        for k in range(len(new_player.weights_2[j])):
                            new_player.weights_2[j][k] += -0.15+random.random()*0.3

                    new_players.append(new_player)

        generation += 1
        print("Generation "+str(generation))        
        players = new_players[0:29]
        global_timer = 0
        screen.fill((255,255,255))
        vision_screen_pxarray[:] = (255,255,255)
        players_remaining = players_start

    pygame.display.flip()
    
    global_timer += 1