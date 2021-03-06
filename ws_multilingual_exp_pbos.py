import contextlib
import logging
import multiprocessing as mp
import os
from collections import ChainMap

import pbos_train
import subwords
from datasets import (prepare_target_vector_paths, prepare_polyglot_freq_paths, prepare_ws_dataset_paths,
                      get_ws_dataset_names, prepare_ws_combined_query_path)
from pbos_pred import predict
from utils import dotdict
from utils.args import dump_args
from ws_eval import eval_ws


def train(args):
    subwords.build_subword_vocab_cli(dotdict(ChainMap(
        dict(word_freq=args.subword_vocab_word_freq, output=args.subword_vocab), args,
    )))

    if args.subword_prob:
        subwords.build_subword_prob_cli(dotdict(ChainMap(
            dict(word_freq=args.subword_prob_word_freq, output=args.subword_prob), args,
        )))

    pbos_train.main(args)


def evaluate(args):
    with open(args.eval_result_path, "w") as fout:
        for bname in get_ws_dataset_names(args.target_vector_name):
            bench_path = prepare_ws_dataset_paths(bname).txt_path
            for lower in (True, False):
                print(args.model_type.ljust(10), eval_ws(args.pred_path, bench_path, lower=lower, oov_handling='zero'),
                      file=fout)


def exp(model_type, target_vector_name):
    target_vector_paths = prepare_target_vector_paths(f"wiki2vec-{target_vector_name}")
    args = dotdict()

    # misc
    args.results_dir = f"results/ws_multi/{target_vector_name}_{model_type}"
    args.model_type = model_type
    args.log_level = "INFO"
    args.target_vector_name = target_vector_name

    # subword
    if model_type == "bos":
        args.word_boundary = True
    elif model_type in ('pbos', 'pbosn'):
        args.word_boundary = False
    args.subword_min_count = None
    args.subword_uniq_factor = None
    if model_type == 'bos':
        args.subword_min_len = 3
        args.subword_max_len = 6
    elif model_type in ('pbos', 'pbosn'):
        args.subword_min_len = 1
        args.subword_max_len = None

    # subword vocab
    args.subword_vocab_max_size = None
    args.subword_vocab_word_freq = target_vector_paths.word_freq_path
    args.subword_vocab = f"{args.results_dir}/subword_vocab.jsonl"

    # subword prob
    args.subword_prob_take_root = False
    if model_type == 'bos':
        args.subword_prob = None
    elif model_type in ('pbos', 'pbosn'):
        args.subword_prob_min_prob = 0
        args.subword_prob_word_freq = prepare_polyglot_freq_paths(target_vector_name).word_freq_path
        args.subword_prob = f"{args.results_dir}/subword_prob.jsonl"

    # training
    args.target_vectors = target_vector_paths.pkl_emb_path
    args.model_path = f"{args.results_dir}/model.pkl"
    args.epochs = 50
    args.lr = 1
    args.lr_decay = True
    args.random_seed = 42
    args.subword_prob_eps = 0.01
    args.subword_weight_threshold = None
    if args.model_type == 'pbosn':
        args.normalize_semb = True
    else:
        args.normalize_semb = False

    # prediction & evaluation
    args.eval_result_path = f"{args.results_dir}/result.txt"
    args.pred_path = f"{args.results_dir}/vectors.txt"
    os.makedirs(args.results_dir, exist_ok=True)

    # redirect log output
    log_file = open(f"{args.results_dir}/info.log", "w+")
    logging.basicConfig(level=logging.INFO, stream=log_file)
    dump_args(args)

    with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
        train(args)

        combined_query_path = prepare_ws_combined_query_path(args.target_vector_name)

        predict(
            model=args.model_path,
            queries=combined_query_path,
            save=args.pred_path,
            word_boundary=args.word_boundary,
        )

        evaluate(args)


if __name__ == '__main__':
    model_types = ("bos", "pbos")
    target_vector_names = ("en", "de", "it", "ru", )

    for target_vector_name in target_vector_names:  # avoid race condition
        prepare_target_vector_paths(f"wiki2vec-{target_vector_name}")
        prepare_polyglot_freq_paths(target_vector_name)

    with mp.Pool() as pool:
        results = [
            pool.apply_async(exp, (model_type, target_vector_name))
            for target_vector_name in target_vector_names
            for model_type in model_types
        ]

        for r in results:
            r.get()
