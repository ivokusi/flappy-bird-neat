import neat.nn.feed_forward
import neat.population
from assets import add_asset

import pygame
import random
import neat
import time
import os

# Game dimensions

WIN_WIDTH = 575
WIN_HEIGHT = 800

pygame.font.init()

GEN = 0

STAT_FONT = pygame.font.SysFont("comicsans", 50)

# Add image assets

BIRD_ASSETS = [add_asset(asset_name) for asset_name in ["bird1.png", "bird2.png", "bird3.png"]]
BACKGROUND_ASSET = add_asset("background.png")
GROUND_ASSET = add_asset("ground.png")
PIPE_ASSET = add_asset("pipe.png")

class Bird:

    ASSETS = BIRD_ASSETS
    MAX_ROTATION = 25 # Bird tilt
    ROTATION_VELOCITY = 20 # Tilt each frame
    ANIMATION_TIME = 5 # Time for each bird asset

    ACCELERATION = 3
    JUMP_VELOCITY = -10.5

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.tilt = 0 # Starts looking horizontally
        self.tick_count = 0 # When we last jumped
        
        self.velocity = 0
        self.height = y
        
        self.asset_count = 0
        self.asset = self.ASSETS[0]

    def jump(self):

        self.velocity = self.JUMP_VELOCITY # up: -y, down: +y
        self.tick_count = 0
        self.height = self.y

    def move(self):
        
        self.tick_count += 1 # one frame passed
        displacement = self.velocity * self.tick_count + 0.5 * self.ACCELERATION * self.tick_count ** 2 # s = ut + 1/2 at^2

        if displacement >= 16:
            displacement = 16
        
        if displacement < 0:
            displacement -= 2
        
        self.y += displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY
    
    def draw(self, window):

        self.asset_count += 1

        # Get appropriate bird asset
        
        if self.asset_count < self.ANIMATION_TIME:
            self.asset = self.ASSETS[0]
        elif self.asset_count < self.ANIMATION_TIME * 2:
            self.asset = self.ASSETS[1]
        elif self.asset_count < self.ANIMATION_TIME * 3:
            self.asset = self.ASSETS[2]
        elif self.asset_count < self.ANIMATION_TIME * 4:
            self.asset = self.ASSETS[1]
        elif self.asset_count == self.ANIMATION_TIME * 4 + 1:
            self.asset = self.ASSETS[0]
            self.asset_count = 0
        
        if self.tilt <= -80:
            self.asset = self.ASSETS[1]
            self.asset_count = self.ANIMATION_TIME * 2

        # Rotate and center image

        rotated_asset = pygame.transform.rotate(self.asset, self.tilt)
        new_rectangle = rotated_asset.get_rect(center=self.asset.get_rect(topleft=(self.x, self.y)).center)    
        window.blit(rotated_asset, new_rectangle.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.asset)

class Pipe:
    
    GAP = 200
    VELOCITY = 5

    def __init__(self, x):
        
        self.x = x
        self.height = 0
        
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_ASSET, False, True)
        self.PIPE_BOTTOM = PIPE_ASSET

        self.passed = False
        self.set_height()
    
    def set_height(self):
        
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):

        self.x -= self.VELOCITY

    def draw(self, window):

        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    def collide(self, bird):

        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        if t_point or b_point:
            return True
    
        return False

class Ground:

    VELOCITY = 5
    WIDTH = GROUND_ASSET.get_width()
    GROUND_ASSET = GROUND_ASSET

    def __init__(self, y):

        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):

        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):

        window.blit(GROUND_ASSET, (self.x1, self.y))
        window.blit(GROUND_ASSET, (self.x2, self.y))

def draw_window(window, birds, pipes, ground, score, generation):
    
    window.blit(BACKGROUND_ASSET, (0, 0))

    for pipe in pipes:
        pipe.draw(window)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(generation), 1, (255, 255, 255))
    window.blit(text, (10, 10))

    ground.draw(window)

    for bird in birds:
        bird.draw(window)
    
    pygame.display.update()

def main(genomes, config):

    global GEN
    GEN += 1

    nets = []
    birds = []
    ge = []

    for _, g in genomes:
        
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        
        birds.append(Bird(230, 350))

        g.fitness = 0
        ge.append(g)

    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    
    ground = Ground(730)
    pipes = [Pipe(600)]

    clock = pygame.time.Clock()

    score = 0
    
    run = True
    while run:
        
        clock.tick(30)

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        add_pipe = False

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()
        
        remove = []
        for pipe in pipes:

            for x, bird in enumerate(birds):
            
                if pipe.collide(bird):
                    
                    ge[x].fitness -= 1
                    
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    remove.append(pipe)

            pipe.move()

        if add_pipe:
            
            score += 1

            for g in ge:
                g.fitness += 5

            pipes.append(Pipe(600))

        for r in remove:
            pipes.remove(r)
        
        for x, bird in enumerate(birds):

            if bird.y + bird.asset.get_height() > 730 or bird.y < 0:
                    
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        ground.move()

        draw_window(window, birds, pipes, ground, score, GEN)

def run(config_file):
    
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, "config-feedforward.txt")
    run(config_file)