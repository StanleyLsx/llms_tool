from typing import Literal, Optional, List, Union
from dataclasses import asdict, dataclass, field
from transformers import Seq2SeqTrainingArguments

# （待完成）预训练：          pretrain
# 模型指令微调：             train_supervised_fine_tuning
# （ing）奖励模型训练：       train_reward_model
# （待完成）奖励模型强化训练：   train_ppo_model
# 网页端测试模型：            web_inference
# 终端模型交互：             terminal_inference
# 融合模型：                merge_peft_model
# 打印模型参数：             show_model_info
# 存储量化的模型：            save_quantized_model
# 模型效果测试及评估：         batch_test
mode = 'train_supervised_fine_tuning'


@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune.
    """
    model_type: str = field(
        default='chatglm',
        metadata={
            # 模型类型
            'help': 'Model type.',
            'choices': ['chatglm', 'llama', 'falcon', 'baichuan', 'aquila', 'internlm', 'moss', 'bloom', 'rwkv'],
        }
    )
    model_path: str = field(
        default='/home/lishouxian/Projects/llm_models/ChatGLM2-6B/fp16',
        metadata={
            # 从huggingface.co/models上下载的模型保存到本地的路径。
            'help': 'Local path to pretrained model or model identifier from huggingface.co/models.'
        }
    )
    checkpoint_dir: Optional[str] = field(
        default=None,
        metadata={
            # 保存下载的或者自己训练的adapter增量模型的地方。
            'help': 'Path to save the (delta) model checkpoints as well as the configurations automatically.',
        }
    )
    cache_dir: Optional[str] = field(
        default=None,
        metadata={
            # 存储从huggingface上下载的临时的模型文件，一般不用管。
            'help': 'Where do you want to store the pretrained models downloaded from huggingface.co',
        },
    )
    use_fast_tokenizer: Optional[bool] = field(
        default=False,
        metadata={
            # 是否使用fast tokenizer，该参数只在llama类模型生效。
            'help': 'Whether to use one of the fast tokenizer (backed by the tokenizers library) or not.',
        }
    )
    padding_side: Optional[str] = field(
        default='right',
        metadata={
            # 有些模型该参数由相应的tokenizer_config.json文件提供，没有的要自己提供。
            'help': 'Padding side.',
            'choices': ['left', 'right'],
        }
    )
    torch_dtype: Optional[str] = field(
        default='float16',
        metadata={
            # 默认就好。
            'help': "Override the default `torch.dtype` and load the model under this dtype. If `auto` is passed, "
                    "the dtype will be automatically derived from the model's weights.",
            'choices': ['auto', 'bfloat16', 'float16', 'float32'],
        }
    )
    quantization: Optional[str] = field(
        default='bnb',
        metadata={
            # 如果使用qlora只能选择bnb，两种量化方式区别不大。
            'help': 'The specific model version to use (can be a branch name, tag name or commit id).',
            'choices': ['cpm', 'bnb'],
        }
    )
    quantization_bit: Optional[int] = field(
        default=None,
        metadata={
            # 使用8bit量化还是4bit量化？
            'help': 'The number of bits to quantize the model.',
            'choices': [4, 8],
        }
    )
    quantization_type: Optional[Literal['fp4', 'nf4']] = field(
        default='nf4',
        metadata={
            # 默认就好
            'help': 'Quantization data type to use in int4 training.',
            'choices': ['fp4', 'nf4']
        }
    )
    double_quantization: Optional[bool] = field(
        default=True,
        metadata={
            # 默认就好
            'help': 'Whether to use double quantization in int4 training or not.',
        }
    )
    cpm_quantization_target: Optional[str] = field(
        default='query_key_value',
        metadata={
            # 需要对这个模型里面的哪些线性层进行量化？
            'help': "Name(s) of target modules to use cpm Quantize. Use comma to separate multiple modules.\
            ChatGLM choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"], \
            Falcon choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"], \
            BLOOM choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"],\
            LLaMA choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"down_proj\", \"up_proj\"],\
            InternLM choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"] \
            Aquila choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"down_proj\", \"up_proj\"] \
            Baichuan choices: [\"W_pack\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"]",
        }
    )
    gradio_port: Optional[int] = field(
        default=1234,
        metadata={
            # 使用web_inference进行交互时候，网页的端口号。
            'help': 'The port id of gradio.'
        }
    )
    quantized_or_merged_output_dir: Optional[str] = field(
        default=None,
        metadata={
            # 当你想保存量化后的模型或者融合后的模型时，处理后的模型保存的地址。
            'help': 'Path to save the quantized or merged model checkpoints as well as the configurations manually.',
        }
    )

    def __post_init__(self):
        import torch
        if isinstance(self.cpm_quantization_target, str):
            self.quantization_target = [target.strip() for target in self.cpm_quantization_target.split(',')]

        if self.torch_dtype in ('auto', None):
            self.torch_dtype = self.torch_dtype
        else:
            self.torch_dtype = getattr(torch, self.torch_dtype)

        if self.quantization_bit is not None:
            assert self.quantization_bit in [4, 8], 'We only accept 4-bit or 8-bit quantization.'


@dataclass
class DataTrainingArguments:
    """
    Arguments pertaining to what data we are going to input our model for training and evaluation.
    """
    train_file_dir: Optional[str] = field(
        default='datasets/finetune/train',
        metadata={
            # 训练集保存的路径。
            'help': 'The train json data file folder.'
        }
    )
    validation_file_dir: Optional[str] = field(
        default='datasets/finetune/test',
        metadata={
            # 验证集保存的路径。
            'help': 'The evaluation json file folder.'
        }
    )
    test_file: Optional[str] = field(
        default='datasets/finetune/test/test_data.json',
        metadata={
            # 测试集保存的路径。
            'help': 'The test file.'
        }
    )
    dev_ratio: Optional[float] = field(
        default=0,
        metadata={
            # 如果要验证模型结果，但是又没有数据集，愿意从训练集拿多少比例的数据给验证集？
            'help': 'Proportion of the dataset to include in the development set, should be between 0.0 and 1.0.'
        }
    )
    prompt_template: Optional[str] = field(
        default='chatglm',
        metadata={
            # 选择对应模型的模板prompt，一般Chat模型的出品方都会有一个固定的prompt。
            'help': 'Which template to use for constructing prompts in training and inference.'
        }
    )
    overwrite_cache: Optional[bool] = field(
        default=True,
        metadata={
            # 是否重写本地保存的huggingface下载的临时模型文件
            'help': 'Overwrite the cached training and evaluation sets.'
        }
    )
    preprocessing_num_workers: Optional[int] = field(
        default=None,
        metadata={
            # 处理数据的时候进程中的worker数，默认就好。
            'help': 'The number of processes to use for the preprocessing.'
        }
    )
    max_input_token: int = field(
        default=2048,
        metadata={
            'help': 'Max token of input.'
        }
    )
    ignore_pad_token_for_loss: Optional[bool] = field(
        default=True,
        metadata={
            # 是否让label里面的padding部分不参与计算。
            'help': 'Whether to ignore the tokens corresponding to padded labels in the loss computation or not.'
        }
    )


@dataclass
class TrainingArguments(Seq2SeqTrainingArguments):
    fine_tuning_type: Optional[str] = field(
        default='lora',
        metadata={
            'help': 'Which fine-tuning method to use.',
            'choices': ['full', 'lora', 'adalora', 'prompt_tuning', 'p_tuning', 'prefix_tuning']
        }
    )
    output_dir: str = field(
        default='checkpoint/adapter_model',
        metadata={
            'help': 'The output directory where the model predictions and checkpoints will be written.'
        }
    )
    do_train: bool = field(
        default=True,
        metadata={
            'help': 'Whether to run training.'
        }
    )
    do_eval: bool = field(
        default=False,
        metadata={
            'help': 'Whether to run eval on the dev set.'
        }
    )
    predict_with_generate: bool = field(
        default=True,
        metadata={
            'help': 'Whether to use generate to calculate generative metrics (ROUGE, BLEU).'
        }
    )
    num_train_epochs: float = field(
        default=10.0,
        metadata={
            'help': 'Total number of training epochs to perform.'
        }
    )
    per_device_train_batch_size: Optional[int] = field(
        default=2,
        metadata={
            'help': 'Batch size per GPU/TPU core/CPU for training.'
        }
    )
    per_device_eval_batch_size: Optional[int] = field(
        default=2,
        metadata={
            'help': 'Batch size per GPU/TPU core/CPU for evaluation.'
        }
    )
    resume_from_checkpoint: Optional[Union[str, bool]] = field(
        default=True,
        metadata={
            'help': 'Continue train model from your checkpoint.'
        }
    )
    gradient_accumulation_steps: Optional[int] = field(
        default=2,
        metadata={
            'help': 'Number of updates steps to accumulate before performing a backward/update pass.'
        }
    )
    gradient_checkpointing: bool = field(
        default=True,
        metadata={
            'help': 'If True, use gradient checkpointing to save memory at the expense of slower backward pass.'
        }
    )
    optim: Optional[str] = field(
        default='adamw_torch',
        metadata={
            'help': 'The optimizer to use.',
            'choices': ['adamw_hf', 'adamw_torch', 'adamw_torch_fused', 'adamw_apex_fused', 'adamw_anyprecision']
        }
    )
    lr_scheduler_type: Optional[str] = field(
        default='cosine',
        metadata={
            'help': 'The scheduler type to use.'
        }
    )
    learning_rate: float = field(
        default=1e-3,
        metadata={
            'help': 'The initial learning rate for AdamW.'
        }
    )
    warmup_steps: int = field(
        default=0,
        metadata={
            'help': 'Linear warmup over warmup_steps.'
        }
    )
    warmup_ratio: float = field(
        default=0.0,
        metadata={
            'help': 'Linear warmup over warmup_ratio fraction of total steps.'
        }
    )
    fp16: bool = field(
        default=True,
        metadata={'help': 'Whether to use fp16 (mixed) precision instead of 32-bit'},
    )
    weight_decay: float = field(
        default=0.0,
        metadata={
            'help': 'Weight decay for AdamW if we apply some.'
        }
    )
    evaluation_strategy: str = field(
        default='no',
        metadata={
            'help': 'The evaluation strategy to use.'
        }
    )
    eval_steps: Optional[float] = field(
        default=None,
        metadata={
            'help': (
                'Run an evaluation every X steps. Should be an integer or a float in range `[0,1)`.'
                'If smaller than 1, will be interpreted as ratio of total training steps.'
            )
        }
    )
    save_steps: float = field(
        default=1000,
        metadata={
            'help': (
                'Save checkpoint every X updates steps. Should be an integer or a float in range `[0,1)`.'
                'If smaller than 1, will be interpreted as ratio of total training steps.'
            )
        },
    )
    save_strategy: str = field(
        default='steps',
        metadata={
            'help': 'The checkpoint save strategy to use.'
        }
    )
    save_total_limit: Optional[int] = field(
        default=None,
        metadata={
            'help': 'Limit the total amount of checkpoints. Deletes the older checkpoints in the output_dir. '
                    'Default is unlimited checkpoints'
        }
    )
    overwrite_output_dir: bool = field(
        default=False,
        metadata={
            'help': 'Overwrite the content of the output directory. '
                    'Use this to continue training if output_dir points to a checkpoint directory.'
        }
    )
    ddp_timeout: Optional[int] = field(
        default=1800,
        metadata={
            'help': 'Overrides the default timeout for distributed training (value should be given in seconds).'
        },
    )
    deepspeed: Optional[str] = field(
        default=None,
        metadata={
            'help': 'Enable deepspeed and pass the path to deepspeed json config file (e.g. ds_config.json) '
                    'or an already loaded json file as a dict'
        }
    )
    report_to: Optional[List[str]] = field(
        default=None,
        metadata={
            'help': 'The list of integrations to report the results and logs to.'
        }
    )
    logging_strategy: str = field(
        default='steps',
        metadata={
            'help': 'The logging strategy to use.'
        }
    )
    logging_steps: float = field(
        default=10,
        metadata={
            'help': (
                'Log every X updates steps. Should be an integer or a float in range `[0,1)`.'
                'If smaller than 1, will be interpreted as ratio of total training steps.'
            )
        },
    )
    logging_first_step: bool = field(
        default=False,
        metadata={
            'help': 'Log the first global_step'
        }
    )
    # 下面都是peft的设置参数
    # Lora:
    lora_rank: Optional[int] = field(
        default=8,
        metadata={
            'help': 'The intrinsic dimension for LoRA fine-tuning.'
        }
    )
    lora_alpha: Optional[float] = field(
        default=32.0,
        metadata={
            'help': 'The scale factor for LoRA fine-tuning (similar with the learning rate).'
        }
    )
    lora_dropout: Optional[float] = field(
        default=0.1,
        metadata={
            'help': 'Dropout rate for the LoRA fine-tuning.'
        }
    )
    # AdaLora:
    adalora_beta: Optional[float] = field(
        default=0.85,
        metadata={
            'help': 'The hyperparameter of EMA for sensitivity smoothing and quantification.'
        }
    )
    adalora_init_r: Optional[int] = field(
        default=12,
        metadata={
            'help': 'The initial rank for each incremental matrix.'
        }
    )
    adalora_tinit: Optional[int] = field(
        default=200,
        metadata={
            'help': 'The steps of initial fine-tuning warmup.'
        }
    )
    adalora_tfinal: Optional[int] = field(
        default=1000,
        metadata={
            'help': 'The step of final fine-tuning.'
        }
    )
    adalora_delta_t: Optional[int] = field(
        default=10,
        metadata={
            'help': 'The time internval between two budget allocations.'
        }
    )
    lora_bias: Optional[str] = field(
        default='none',
        metadata={
            'help': "Bias type for Lora. Can be 'none', 'all' or 'lora_only'",
            'choices': ['none', 'all', 'lora_only']
        }
    )
    lora_target: Optional[str] = field(
        default='query_key_value',
        metadata={
            'help': "Name(s) of target modules to use cpm Quantize. Use comma to separate multiple modules.\
            ChatGLM choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"], \
            Falcon choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"], \
            BLOOM choices: [\"query_key_value\", \"self_attention.dense\", \"dense_h_to_4h\", \"dense_4h_to_h\"],\
            LLaMA choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"down_proj\", \"up_proj\"],\
            InternLM choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"] \
            Aquila choices: [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"down_proj\", \"up_proj\"] \
            Baichuan choices: [\"W_pack\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"]"
        }
    )
    # prompt_tuning:
    num_virtual_tokens: Optional[int] = field(
        default=20,
        metadata={
            'help': 'Number of virtual tokens.'
        }
    )
    prompt_encoder_hidden_size: Optional[int] = field(
        default=128,
        metadata={
            'help': 'The hidden size of the prompt encoder'
        }
    )


@dataclass
class GeneratingArguments:
    """
    Arguments pertaining to specify the decoding parameters.
    """
    do_sample: Optional[bool] = field(
        default=True,
        metadata={'help': 'Whether or not to use sampling, use greedy decoding otherwise.'}
    )
    temperature: Optional[float] = field(
        default=0.95,
        metadata={'help': 'The value used to modulate the next token probabilities.'}
    )
    top_p: Optional[float] = field(
        default=0.7,
        metadata={
            'help': 'The smallest set of most probable tokens with '
                    'probabilities that add up to top_p or higher are kept.'}
    )
    top_k: Optional[int] = field(
        default=50,
        metadata={'help': 'The number of highest probability vocabulary tokens to keep for top-k filtering.'}
    )
    num_beams: Optional[int] = field(
        default=1,
        metadata={'help': 'Number of beams for beam search. 1 means no beam search.'}
    )
    max_length: Optional[int] = field(
        default=None,
        metadata={'help': 'The whole numbers of output tokens, including the number of tokens in the prompt.'}
    )
    max_new_tokens: Optional[int] = field(
        default=512,
        metadata={'help': 'The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.'}
    )
    repetition_penalty: Optional[float] = field(
        default=1.0,
        metadata={'help': 'The parameter for repetition penalty. 1.0 means no penalty.'}
    )

    def to_dict(self):
        args = asdict(self)
        if args.get('max_new_tokens', None):
            args.pop('max_length', None)
        return args
