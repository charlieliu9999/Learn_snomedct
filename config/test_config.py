# SNOMED CT测试配置文件

# Ollama配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "medgemma:latest",
    "timeout": 120,
    "max_retries": 3,
    "generation_options": {
        "temperature": 0.1,  # 降低随机性
        "top_p": 0.9,
        "num_predict": 2048
    }
}

# 评估配置
EVALUATION_CONFIG = {
    "entity_weight": 0.4,
    "structure_weight": 0.3,
    "coding_weight": 0.3,
    "passing_score": 0.7,  # 及格分数
    "excellent_score": 0.8  # 优秀分数
}

# 优化配置
OPTIMIZATION_CONFIG = {
    "max_iterations": 3,
    "improvement_threshold": 0.05,  # 最小改进幅度
    "convergence_threshold": 0.8,   # 收敛阈值
    "failure_score_threshold": 0.7  # 失败案例阈值
}

# 测试数据配置
TEST_DATA_CONFIG = {
    "test_dataset_path": "data/medical_test_dataset.json",
    "results_dir": "results",
    "prompts_dir": "prompts"
}

# 日志配置
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    "save_detailed_logs": True
} 