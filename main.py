import os
import pygame
import gymnasium as gym
import numpy as np

import time

from env import CheckersEnv
from env import Board
from env import Piece

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy


def train():
    env = CheckersEnv(render_mode="human", render_fps=60)
    env = DummyVecEnv([lambda:env])
    model = PPO('MlpPolicy', env=env, verbose=1)
    model.learn(total_timesteps=81920)

    model_file_name = 'ppo_model_checkers'
    ppo_path = os.path.join('models', model_file_name)
    model.save(ppo_path)

    env.close()


def evaluate():
    model_file_name = 'ppo_model_checkers'
    ppo_path = os.path.join('models', model_file_name)

    env = CheckersEnv(render_mode="human", render_fps=1)
    env = DummyVecEnv([lambda:env])
    model = PPO.load(ppo_path, env=env)

    evaluate_policy(model, env, n_eval_episodes=10, render=True)

    env.close()


def test():
    env = CheckersEnv(render_mode="human", render_fps=1)
    obs, info = env.reset()

    print(obs)
    print(env.action_space.sample())

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


def debug():
    env = CheckersEnv(render_mode="human")
    state, info = env.reset()

    env.board.pieces = [[], [], [], [], [], [], [], []]
    print(env.board.pieces)
    for row in range(8):
            for col in range(8):
                env.board.pieces[row].append(Piece(row, col, 'empty'))
    env.board.pieces[7][2] = Piece(7, 2, 'white')
    env.board.pieces[6][3] = Piece(6, 3, 'black')
    env.board.pieces[4][3] = Piece(4, 3, 'black')
    env.board.jumps = []
    env.board.moves = []
    env.render()
    time.sleep(5.0)
    env.board.turn = 'white'
    env.board.update()
    env.render()
    time.sleep(5.0)

if __name__ == '__main__':

    train()
