from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.report import Patient, MedicalReport, StructuredResult, Entity, Relationship
from src.models.snomed_analyzer import SnomedAnalyzer
import json

report_bp = Blueprint('report', __name__)
snomed_analyzer = SnomedAnalyzer()

@report_bp.route('/analyze', methods=['POST'])
def analyze_report():
    """
    分析医学影像报告并返回结构化结果
    """
    try:
        data = request.json
        
        # 验证必要字段
        required_fields = ['age', 'gender', 'examination_type', 'findings', 'impression']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要字段: {field}'}), 400
        
        # 创建患者记录
        patient = Patient(
            age=data['age'],
            gender=data['gender']
        )
        db.session.add(patient)
        db.session.flush()  # 获取patient_id
        
        # 创建医学报告记录
        raw_text = f"患者年龄: {data['age']}\n患者性别: {data['gender']}\n检查项目: {data['examination_type']}\n影像所见: {data['findings']}\n诊断意见: {data['impression']}"
        report = MedicalReport(
            patient_id=patient.id,
            examination_type=data['examination_type'],
            findings=data['findings'],
            impression=data['impression'],
            raw_text=raw_text
        )
        db.session.add(report)
        db.session.flush()  # 获取report_id
        
        # 分析影像所见
        findings_result = snomed_analyzer.analyze_text(data['findings'], 'findings')
        findings_structured = StructuredResult(
            report_id=report.id,
            section='findings'
        )
        db.session.add(findings_structured)
        db.session.flush()
        
        # 保存影像所见的实体
        findings_entities = {}
        for entity_data in findings_result.get('entities', []):
            entity = Entity(
                structured_result_id=findings_structured.id,
                text=entity_data.get('text', ''),
                entity_type=entity_data.get('entity_type', ''),
                snomed_code=entity_data.get('snomed_code'),
                snomed_term=entity_data.get('snomed_term'),
                start_pos=entity_data.get('start_pos'),
                end_pos=entity_data.get('end_pos')
            )
            db.session.add(entity)
            db.session.flush()
            findings_entities[entity_data.get('id')] = entity.id
        
        # 保存影像所见的关系
        for rel_data in findings_result.get('relationships', []):
            source_id = findings_entities.get(rel_data.get('source_id'))
            target_id = findings_entities.get(rel_data.get('target_id'))
            
            if source_id and target_id:
                relationship = Relationship(
                    structured_result_id=findings_structured.id,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=rel_data.get('relation_type', ''),
                    snomed_relation_code=rel_data.get('snomed_relation_code')
                )
                db.session.add(relationship)
        
        # 分析诊断意见
        impression_result = snomed_analyzer.analyze_text(data['impression'], 'impression')
        impression_structured = StructuredResult(
            report_id=report.id,
            section='impression'
        )
        db.session.add(impression_structured)
        db.session.flush()
        
        # 保存诊断意见的实体
        impression_entities = {}
        for entity_data in impression_result.get('entities', []):
            entity = Entity(
                structured_result_id=impression_structured.id,
                text=entity_data.get('text', ''),
                entity_type=entity_data.get('entity_type', ''),
                snomed_code=entity_data.get('snomed_code'),
                snomed_term=entity_data.get('snomed_term'),
                start_pos=entity_data.get('start_pos'),
                end_pos=entity_data.get('end_pos')
            )
            db.session.add(entity)
            db.session.flush()
            impression_entities[entity_data.get('id')] = entity.id
        
        # 保存诊断意见的关系
        for rel_data in impression_result.get('relationships', []):
            source_id = impression_entities.get(rel_data.get('source_id'))
            target_id = impression_entities.get(rel_data.get('target_id'))
            
            if source_id and target_id:
                relationship = Relationship(
                    structured_result_id=impression_structured.id,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=rel_data.get('relation_type', ''),
                    snomed_relation_code=rel_data.get('snomed_relation_code')
                )
                db.session.add(relationship)
        
        # 提交所有更改
        db.session.commit()
        
        # 返回结构化结果
        result = {
            'report_id': report.id,
            'findings': findings_result,
            'impression': impression_result
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@report_bp.route('/reports', methods=['GET'])
def get_reports():
    """
    获取所有医学报告的历史记录
    """
    try:
        reports = MedicalReport.query.order_by(MedicalReport.created_at.desc()).all()
        reports_data = []
        
        for report in reports:
            report_data = report.to_dict()
            # 简化返回数据，不包含原始文本
            report_data.pop('raw_text', None)
            reports_data.append(report_data)
        
        return jsonify(reports_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    """
    获取特定医学报告的详细信息，包括结构化结果
    """
    try:
        report = MedicalReport.query.get(report_id)
        if not report:
            return jsonify({'error': '报告不存在'}), 404
        
        report_data = report.to_dict()
        
        # 获取结构化结果
        structured_results = StructuredResult.query.filter_by(report_id=report_id).all()
        structured_data = {}
        
        for result in structured_results:
            result_data = result.to_dict()
            structured_data[result.section] = result_data
        
        report_data['structured_results'] = structured_data
        
        return jsonify(report_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
