from datetime import datetime
from src.models.user import db

class Patient(db.Model):
    """患者信息模型"""
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    reports = db.relationship('MedicalReport', backref='patient', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MedicalReport(db.Model):
    """医学影像报告模型"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    examination_type = db.Column(db.String(100), nullable=False)  # 检查项目
    findings = db.Column(db.Text, nullable=False)  # 影像所见
    impression = db.Column(db.Text, nullable=False)  # 诊断意见
    raw_text = db.Column(db.Text, nullable=False)  # 原始文本
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    structured_results = db.relationship('StructuredResult', backref='report', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'examination_type': self.examination_type,
            'findings': self.findings,
            'impression': self.impression,
            'raw_text': self.raw_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'patient': self.patient.to_dict() if self.patient else None
        }

class StructuredResult(db.Model):
    """SNOMED CT结构化结果模型"""
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('medical_report.id'), nullable=False)
    section = db.Column(db.String(20), nullable=False)  # 'findings' 或 'impression'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    entities = db.relationship('Entity', backref='structured_result', lazy=True)
    relationships = db.relationship('Relationship', backref='structured_result', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'section': self.section,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'entities': [entity.to_dict() for entity in self.entities],
            'relationships': [rel.to_dict() for rel in self.relationships]
        }

class Entity(db.Model):
    """SNOMED CT实体模型"""
    id = db.Column(db.Integer, primary_key=True)
    structured_result_id = db.Column(db.Integer, db.ForeignKey('structured_result.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)  # 原文中的实体文本
    entity_type = db.Column(db.String(50), nullable=False)  # 实体类型
    snomed_code = db.Column(db.String(50), nullable=True)  # SNOMED CT编码
    snomed_term = db.Column(db.String(255), nullable=True)  # SNOMED CT标准术语
    start_pos = db.Column(db.Integer, nullable=True)  # 在原文中的起始位置
    end_pos = db.Column(db.Integer, nullable=True)  # 在原文中的结束位置
    
    def to_dict(self):
        return {
            'id': self.id,
            'structured_result_id': self.structured_result_id,
            'text': self.text,
            'entity_type': self.entity_type,
            'snomed_code': self.snomed_code,
            'snomed_term': self.snomed_term,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos
        }

class Relationship(db.Model):
    """SNOMED CT关系模型"""
    id = db.Column(db.Integer, primary_key=True)
    structured_result_id = db.Column(db.Integer, db.ForeignKey('structured_result.id'), nullable=False)
    source_entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    target_entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)  # 关系类型
    snomed_relation_code = db.Column(db.String(50), nullable=True)  # SNOMED CT关系编码
    
    # 关联关系
    source_entity = db.relationship('Entity', foreign_keys=[source_entity_id], backref='source_relationships')
    target_entity = db.relationship('Entity', foreign_keys=[target_entity_id], backref='target_relationships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'structured_result_id': self.structured_result_id,
            'source_entity_id': self.source_entity_id,
            'target_entity_id': self.target_entity_id,
            'relation_type': self.relation_type,
            'snomed_relation_code': self.snomed_relation_code,
            'source_entity': self.source_entity.to_dict() if self.source_entity else None,
            'target_entity': self.target_entity.to_dict() if self.target_entity else None
        }
