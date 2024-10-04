import os
import pygame
import gymnasium as gym
import numpy as np

from env import CheckersEnv

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy


def train():
    env = CheckersEnv(render_mode="human")
    env = DummyVecEnv([lambda:env])
    model = PPO('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=10)

    model_file_name = 'ppo_model_checkers'
    ppo_path = os.path.join('models', model_file_name)
    model.save(ppo_path)

    env.close()


def evaluate():
    model_file_name = 'ppo_model_checkers'
    ppo_path = os.path.join('models', model_file_name)

    env = CheckersEnv(render_mode="human")
    env = DummyVecEnv([lambda:env])
    model = PPO.load(ppo_path, env=env)

    evaluate_policy(model, env, n_eval_episodes=10, render=True)

    env.close()


def test():
    env = CheckersEnv(render_mode="human")
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

if __name__ == '__main__':

    train()
