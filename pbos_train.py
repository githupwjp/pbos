from collections import Counter
from itertools import count
from time import time
from random import choice
import os, pickle

import numpy as np
# from tqdm import tqdm

from bos import PBoS
from utils.load import load_vocab
from utils.preprocess import normalize_prob

import argparse, datetime, json, logging, os
parser = argparse.ArgumentParser(description='Bag of substrings',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--target', required=True,
    help='pretrained target word vectors')
parser.add_argument('--save', default="./results/run_{timestamp}/model.pbos",
    help='save path')
parser.add_argument('--loglevel', default='INFO',
    help='log level used by logging module')
training_group = parser.add_argument_group('training arguments')
training_group.add_argument('--epochs', type=int, default=2,
    help='number of training epochs')
training_group.add_argument('--lr', type=float, default=1.0,
    help='learning rate')
training_group.add_argument('--lr_decay', action='store_true',
    help='reduce learning learning rate between epochs')
model_group = parser.add_argument_group('PBoS model arguments')
parser.add_argument('--word_list', '-f', default="./datasets/unigram_freq.csv",
    help="list of words to create subword vocab")
parser.add_argument('--boundary', '-b', action='store_true',
    help="annotate word boundary")
args = parser.parse_args()

numeric_level = getattr(logging, args.loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % args.loglevel)
logging.basicConfig(level=numeric_level)

save_path = args.save.format(timestamp=datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
save_dir, _ = os.path.split(save_path)
try :
    os.makedirs(save_dir)
except FileExistsError :
    logging.warning("Things will get overwritten for directory {}".format(save_dir))

with open(os.path.join(save_dir, 'args.json'), 'w') as fout :
    json.dump(vars(args), fout)

logging.info('loading target vectors...')
_, ext = os.path.splitext(args.target)
if ext in (".txt", ) :
    vocab, emb = [], []
    for i, line in zip(count(1), open(args.target)) :
        ss = line.split()
        vocab.append(ss[0])
        emb.append([float(x) for x in ss[1:]])
        if i % 10000 == 0 :
            logging.info('{} lines loaded'.format(i))
elif ext in (".pickle", ".pkl") :
    vocab, emb = pickle.load(open(args.target, 'rb'))
else :
    raise ValueError('Unsupported target vector file extent: {}'.format(args.target))
emb = np.array(emb)

logging.info(f"building subword vocab from `{args.word_list}`...")
subword_count = load_vocab(args.word_list, boundary=args.boundary)
subword_prob = normalize_prob(subword_count, take_root=True)
logging.info(f"subword vocab size: {len(subword_prob)}")

def MSE(pred, target) :
    return sum((pred - target) ** 2 / 2) / len(target)
def MSE_backward(pred, target) :
    return (pred - target) / len(target)

model = PBoS(embedding_dim=len(emb[0]),
    subword_prob=subword_prob,
    boundary=args.boundary,
)
h = []
start_time = time()
for i_epoch in range(args.epochs) :
    lr = args.lr / (1 + i_epoch) ** 0.5 if args.lr_decay else args.lr
    logging.info('epoch {:>2} / {} | lr {:.5f}'.format(1 + i_epoch, args.epochs, lr))
    epoch_start_time = time()
    for i_inst, wi in zip(count(1), np.random.choice(len(vocab), len(vocab), replace=False)) :
        w = vocab[wi]
        e = model.embed(w)
        tar = emb[wi]
        g = MSE_backward(e, tar)

        if i_inst % 20 == 0 :
            loss = MSE(e, tar)
            h.append(loss)
        if i_inst % 10000 == 0 :
            width = len(f"{len(vocab)}")
            fmt = 'processed {:%d}/{:%d} | loss {:.5f}' % (width, width)
            logging.info(fmt.format(i_inst, len(vocab), np.average(h)))
            h = []

        d = - lr * g
        model.step(w, d)
    now_time = time()
    logging.info('epoch {i_epoch:>2} / {n_epoch} | time {epoch_time:.2f}s / {training_time:.2f}s'.format(
        i_epoch = 1 + i_epoch, n_epoch = args.epochs,
        epoch_time = now_time - epoch_start_time,
        training_time = now_time - start_time,
    ))

logging.info('saving model...')
model.dump(save_path)