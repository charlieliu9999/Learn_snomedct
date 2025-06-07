import json

MEDICAL_TEST_DATASET = [
    {
        "id": 1,
        "report": "侧大脑半球额、顶、枕、颞叶见大片状低密度区，边界模糊，侧脑室受压，中线结构偏移。脑干及小脑未见异常。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "254829004",
                    "preferred_term": "低密度区",
                    "attributes": {
                        "finding_site": {"term": "大脑半球"},
                        "associated_morphology": {"term": "大片状"},
                        "severity": {"term": "中等"}
                    }
                }
            ],
            "expected_entities": ["低密度区", "大脑半球", "额叶", "顶叶", "枕叶", "颞叶", "脑室受压", "中线结构偏移"],
            "expected_relationships": [
                {"from": "低密度区", "to": "大脑半球", "type": "located_in"}
            ]
        }
    },
    {
        "id": 2,
        "report": "左侧额叶见椭圆形低密度灶，直径约2.5cm，边界清楚，周围无水肿。增强扫描病灶轻度强化。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "254829004",
                    "preferred_term": "低密度灶",
                    "attributes": {
                        "finding_site": {"term": "左侧额叶"},
                        "associated_morphology": {"term": "椭圆形"},
                        "laterality": {"term": "左侧"}
                    }
                }
            ],
            "expected_entities": ["低密度灶", "左侧额叶", "椭圆形", "强化"],
            "expected_relationships": [
                {"from": "低密度灶", "to": "左侧额叶", "type": "located_in"}
            ]
        }
    },
    {
        "id": 3,
        "report": "右侧颞叶内侧见结节状异常信号，T1WI呈低信号，T2WI呈高信号，DWI呈高信号。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "118616009",
                    "preferred_term": "异常信号",
                    "attributes": {
                        "finding_site": {"term": "右侧颞叶"},
                        "associated_morphology": {"term": "结节状"},
                        "laterality": {"term": "右侧"}
                    }
                }
            ],
            "expected_entities": ["异常信号", "右侧颞叶", "结节状", "T1WI", "T2WI", "DWI"],
            "expected_relationships": [
                {"from": "异常信号", "to": "右侧颞叶", "type": "located_in"}
            ]
        }
    },
    {
        "id": 4,
        "report": "双侧基底节区对称性T2高信号，未见明显占位效应。肝豆状核变性可能。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "118616009",
                    "preferred_term": "T2高信号",
                    "attributes": {
                        "finding_site": {"term": "双侧基底节区"},
                        "associated_morphology": {"term": "对称性"},
                        "laterality": {"term": "双侧"}
                    }
                }
            ],
            "expected_entities": ["T2高信号", "双侧基底节区", "对称性", "肝豆状核变性"],
            "expected_relationships": [
                {"from": "T2高信号", "to": "双侧基底节区", "type": "located_in"}
            ]
        }
    },
    {
        "id": 5,
        "report": "小脑蚓部见囊性病变，壁薄，内容物呈脑脊液信号。考虑蛛网膜囊肿。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "441457006",
                    "preferred_term": "囊性病变",
                    "attributes": {
                        "finding_site": {"term": "小脑蚓部"},
                        "associated_morphology": {"term": "囊性"},
                        "severity": {"term": "轻度"}
                    }
                }
            ],
            "expected_entities": ["囊性病变", "小脑蚓部", "囊性", "蛛网膜囊肿"],
            "expected_relationships": [
                {"from": "囊性病变", "to": "小脑蚓部", "type": "located_in"}
            ]
        }
    },
    {
        "id": 6,
        "report": "胼胝体膝部信号异常，T2WI呈高信号，FLAIR呈高信号，考虑脱髓鞘病变。",
        "gold_standard": {
            "clinical_findings": [
                {
                    "concept_id": "52988006",
                    "preferred_term": "脱髓鞘病变",
                    "attributes": {
                        "finding_site": {"term": "胼胝体膝部"},
                        "pathological_process": {"term": "脱髓鞘"},
                        "severity": {"term": "中度"}
                    }
                }
            ],
            "expected_entities": ["脱髓鞘病变", "胼胝体膝部", "信号异常", "T2WI", "FLAIR"],
            "expected_relationships": [
                {"from": "脱髓鞘病变", "to": "胼胝体膝部", "type": "located_in"}
            ]
        }
    }
]

def save_test_dataset():
    """保存测试数据集到JSON文件"""
    with open("data/medical_test_dataset.json", "w", encoding="utf-8") as f:
        json.dump(MEDICAL_TEST_DATASET, f, ensure_ascii=False, indent=2)
    print(f"✅ 测试数据集已保存，包含 {len(MEDICAL_TEST_DATASET)} 个测试案例")

def load_test_dataset():
    """加载测试数据集"""
    try:
        with open("data/medical_test_dataset.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ 测试数据集文件未找到，返回默认数据集")
        return MEDICAL_TEST_DATASET

if __name__ == "__main__":
    save_test_dataset() 