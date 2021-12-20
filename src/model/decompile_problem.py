# coding=utf-8
from tensor2tensor.utils import registry
from tensor2tensor.data_generators import problem, text_problems


@registry.register_problem
class decompile_problem(text_problems.Text2TextProblem):
    @property
    def approx_vocab_size(self):
        return 2 ** 9

    @property
    def is_generate_per_split(self):
        return False

    @property
    def dataset_splits(self):
        return [{
            "split": problem.DatasetSplit.TRAIN,
            "shards": 9,
        }, {
            "split": problem.DatasetSplit.EVAL,
            "shards": 1,
        }]

    def generate_samples(self, data_dir, tmp_dir, dataset_split):
        del data_dir
        del tmp_dir
        del dataset_split
        # 读取原始的训练样本数据
        asm = open("inputs.txt", "r")
        source = open("targets.txt", "r")

        comment_list = asm.readlines()
        tag_list = source.readlines()
        asm.close()
        source.close()
        for comment, tag in zip(comment_list, tag_list):
            comment = comment.strip().lower()
            tag = tag.strip().lower()
            yield {
                "inputs": comment,
                "targets": tag
                }
