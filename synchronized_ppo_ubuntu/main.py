from multi_pipe import SubprocVecEnv
import numpy as np
import time
from trans import trans_data, check_done, get_action, memory_stack
from policy_net import Policy_net
from ppo import PPOTrain
import tensorflow as tf
import matplotlib.pyplot as plt
from collections import deque

#r = tf.placeholder(tf.float32)
#rr = tf.summary.scalar('reward', r)
#merged = tf.summary.merge_all()

def train():  
    num_process = 4
    sub = SubprocVecEnv(num_process, False)
    state_space = 2
    action_space = 4
    Policy = Policy_net('policy', state_space, action_space)
    Old_Policy = Policy_net('old_policy', state_space, action_space)
    PPO = PPOTrain(Policy, Old_Policy, gamma=0.95)
    with tf.Session() as sess:
        saver = tf.train.Saver()
        tf.set_random_seed(1234)
        #sess.run(tf.global_variables_initializer())
        saver.restore(sess, './synch_ubuntu/model')
        i=0
        #writer = tf.summary.FileWriter('./board/dqn_per', sess.graph)
        #for i in range(10):
        while True:
            i += 1
            info = sub.reset()
            terminal, each_terminal = False, [False] * num_process
            global_step = 0
            memory = []
            obs_s, state, action, reward, done = trans_data(info, num_process)
            while not terminal:
                time.sleep(0.05)
                global_step += 1
                action, v_pred = get_action(Policy, each_terminal, num_process, state)
                info = sub.step(action, obs_s, [global_step]*num_process)
                obs_s, next_state, a, reward, done = trans_data(info, num_process)
                each_terminal, terminal = check_done(info, num_process)
                memory.append([state, action, reward, v_pred])

                if terminal:
                    state_, action_, reward_, v_preds_next_, gaes_ = memory_stack(memory, num_process, state_space, PPO)
                    PPO.assign_policy_parameters()
                    inp = [state_, action_, reward_, v_preds_next_, gaes_]
                    for epoch in range(3):
                        sample_indices = np.random.randint(low=0, high=state_.shape[0], size=64)
                        sampled_inp = [np.take(a=t, indices=sample_indices, axis=0) for t in inp]
                        PPO.train(obs=sampled_inp[0],
                            actions=sampled_inp[1],
                            rewards=sampled_inp[2],
                            v_preds_next=sampled_inp[3],
                            gaes=sampled_inp[4])
                    #summary = sess.run(merged, feed_dict={r:sum(reward_)/(num_process)})
                    #writer.add_summary(summary, i)
                    #saver.save(sess, './synch_ubuntu/model')
                    if i < 5100:
                        print(sum(reward_)/(num_process), i)
                state = next_state
        sub.close()

if __name__=='__main__':
    train()


    