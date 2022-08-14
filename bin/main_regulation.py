import gym
import custom_regulation_task

env = gym.make('CustomRegulationTask-v0')

print(env.action_space.sample())