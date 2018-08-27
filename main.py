import time
import argparse
import numpy as np
import tensorflow as tf

from model import charcnn
from config import get_config
from dataloader import Doc2VecEmbeddings, DataLoader, DataIterator


parser = argparse.ArgumentParser(description='train/test movie review classification model')
parser.add_argument('--checkpoint', type=str, help='pre-trained model', default=None)
args = parser.parse_args()

# parsed args
checkpoint = args.checkpoint

# Configuration
config, _ = get_config()

np.random.seed(config.seed)
tf.set_random_seed(config.seed)


if __name__ == '__main__':
    # DataSet Loader
    ds = DataLoader(file=config.processed_dataset,
                    n_classes=config.n_classes,
                    analyzer=config.analyzer,
                    is_analyzed=True,
                    use_save=False,
                    config=config)

    if config.verbose:
        print("[+] DataSet loaded! Total %d samples" % len(ds.labels))

    # DataSet Iterator
    di = DataIterator(x=ds.sentences, y=ds.labels, batch_size=config.batch_size)

    # Doc2Vec Loader
    vec = Doc2VecEmbeddings(config.d2v_model, config.embed_size)
    if config.verbose:
        print("[+] Doc2Vec loaded! Total %d pre-trained sentences, %d dims" % (len(vec), n_dims))

    if config.is_train:
        # GPU configure
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        with tf.Session(config=config) as s:
            if config.model == 'charcnn':
                # Model Loaded
                model = charcnn.CharCNN(s=s,
                                        n_classes=config.n_classes,
                                        dims=config.embed_size)
            else:
                raise NotImplementedError("[-] Not Implemented Yet")

            # Initializing
            s.run(tf.global_variables_initializer())

            print("[*] Reading checkpoints...")

            saved_global_step = 0
            ckpt = tf.train.get_checkpoint_state('./model/')
            if ckpt and ckpt.model_checkpoint_path:
                # Restores from checkpoint
                model.saver.restore(s, ckpt.model_checkpoint_path)

                saved_global_step = int(ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1])
                print("[+] global step : %d" % saved_global_step, " successfully loaded")
            else:
                print('[-] No checkpoint file found')

            start_time = time.time()

            global_step = 0
            for epoch in range(config.epochs):
                for x_train, y_train in di.iterate():
                    # training
                    loss = s.run([model.opt, model.loss],
                                 feed_dict={
                                     model.x: x_train,
                                     model.y: y_train,
                                     model.do_rate: .8,
                                 })

                    if global_step % config.logging_step == 0:
                        print("[*] epoch %d global step %d" % (epoch, global_step), " loss : {:.8f}".format(loss))

                        summary = s.run([model.merged],
                                        feed_dict={
                                            model.x: x_train,
                                            model.y: y_train,
                                            model.do_rate: .0,
                                        })

                        # Summary saver
                        model.writer.add_summary(summary, global_step)

                        # Model save
                        model.saver.save(s, './model/%s.ckpt' % config.model, global_step=global_step)

                    global_step += 1

            end_time = time.time()

            print("[+] Training Done! Elapsed {:.8f}s".format(end_time - start_time))

    else:  # Test
        pass
