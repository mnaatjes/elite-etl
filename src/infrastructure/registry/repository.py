from sqlalchemy.orm import Session
from src.infrastructure.registry.models import Source, Pipeline, DAG, Node, Edge, SourceSchema
import uuid

class SourceRepository:
    @staticmethod
    def create(db: Session, data: dict) -> Source:
        source = Source(**data)
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @staticmethod
    def get_all(db: Session):
        return db.query(Source).all()

    @staticmethod
    def get(db: Session, source_id: uuid.UUID):
        return db.query(Source).filter(Source.id == source_id).first()

    @staticmethod
    def get_latest_schema(db: Session, source_id: uuid.UUID):
        return db.query(SourceSchema).filter(SourceSchema.source_id == source_id).order_by(SourceSchema.version_number.desc()).first()
        
    @staticmethod
    def get_all_approved(db: Session):
        return db.query(Source).all() # Filter omitted for Phase 5 brevity

class PipelineRepository:
    @staticmethod
    def create(db: Session, data: dict) -> Pipeline:
        pipeline = Pipeline(**data)
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline

    @staticmethod
    def get_all(db: Session):
        return db.query(Pipeline).all()

    @staticmethod
    def get(db: Session, pipeline_id: uuid.UUID):
        return db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

class DAGRepository:
    @staticmethod
    def get_active(db: Session, pipeline_id: uuid.UUID):
        return db.query(DAG).filter(DAG.pipeline_id == pipeline_id).order_by(DAG.version_number.desc()).first()

    @staticmethod
    def insert(db: Session, pipeline_id: uuid.UUID, description: str, is_valid: bool, nodes_data: list, edges_data: list) -> DAG:
        latest = db.query(DAG).filter(DAG.pipeline_id == pipeline_id).order_by(DAG.version_number.desc()).first()
        next_ver = (latest.version_number + 1) if latest else 1

        dag = DAG(pipeline_id=pipeline_id, version_number=next_ver, description=description, is_valid=is_valid)
        db.add(dag)
        db.flush()

        for n in nodes_data:
            node = Node(
                id=n["id"],
                dag_id=dag.id,
                label=n["label"],
                type=n["type"],
                bound_schema_id=n.get("bound_schema_id"),
                sql_template=n.get("sql_template"),
                ui_metadata=n.get("ui_metadata"),
                inferred_schema=n.get("inferred_schema")
            )
            db.add(node)
            
        for e in edges_data:
            edge = Edge(
                dag_id=dag.id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id
            )
            db.add(edge)

        db.commit()
        db.refresh(dag)
        return dag
