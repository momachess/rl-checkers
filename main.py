import pygame
from time import sleep

from env import CheckersEnv


def test():
    env = CheckersEnv(render_mode="human")
    obs, info = env.reset()

    episodes = 5
    for episode in range(1, episodes+1):
        terminated = False
        truncated = False
        score = 0

        while not terminated and not truncated:
            action = [0]
            obs, reward, terminated, truncated, info = env.step(action)
            score += reward

            # print(obs, reward)

        obs, info = env.reset()

        print('Episode: {} Score: {}'.format(episode, score))

    env.close()

if __name__ == '__main__':

    test()

    '''
    def register_input():
        global quit
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit = True

            if event.type == pygame.QUIT:
                quit = True

    env = CheckersEnv()
    env.render()

    quit = False
    while not quit:
        while True:
            register_input()
            if env.step() == True:
                sleep(10)
                quit = True
            pygame.display.flip()

            if quit:
                break

    pygame.display.quit()
    pygame.quit()
    '''