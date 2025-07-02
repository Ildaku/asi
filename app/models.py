from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum as SQLAlchemyEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import db
import enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class PlanStatus(str, enum.Enum):
    DRAFT = "черновик"
    APPROVED = "утверждён"
    IN_PROGRESS = "в производстве"
    COMPLETED = "завершен"
    CANCELLED = "отменен"

    @property
    def display(self):
        return {
            PlanStatus.DRAFT: "Черновик",
            PlanStatus.APPROVED: "Утверждён",
            PlanStatus.IN_PROGRESS: "В производстве",
            PlanStatus.COMPLETED: "Завершен",
            PlanStatus.CANCELLED: "Отменен"
        }[self]

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLAlchemyEnum(UserRole))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_operator(self):
        return self.role == UserRole.OPERATOR

class RawMaterialType(db.Model):
    __tablename__ = "raw_material_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    raw_materials = relationship("RawMaterial", back_populates="type")
    recipe_items = relationship("RecipeItem", back_populates="material_type")

class RawMaterial(db.Model):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type_id = Column(Integer, ForeignKey("raw_material_types.id"))
    batch_number = Column(String)
    quantity_kg = Column(Float)
    date_received = Column(DateTime(timezone=True))
    expiration_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    type = relationship("RawMaterialType", back_populates="raw_materials")
    batches = relationship("MaterialBatch", back_populates="material")

    def get_usage(self):
        """Возвращает общее количество использованного сырья в килограммах"""
        total_usage = 0.0
        for batch in self.batches:
            for batch_material in batch.batch_materials:
                total_usage += batch_material.quantity
        return total_usage

    def get_batch_count(self):
        """Возвращает количество замесов, в которых использовалось сырье"""
        unique_batches = set()
        for batch in self.batches:
            for batch_material in batch.batch_materials:
                unique_batches.add(batch_material.batch_id)
        return len(unique_batches)

class MaterialBatch(db.Model):
    __tablename__ = "material_batches"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("raw_materials.id"))
    batch_number = Column(String)
    quantity = Column(Float)
    remaining_quantity = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    material = relationship("RawMaterial", back_populates="batches")
    batch_materials = relationship("BatchMaterial", back_populates="material_batch")

class Product(db.Model):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    recipe_templates = relationship("RecipeTemplate", back_populates="product")
    production_plans = relationship("ProductionPlan", back_populates="product")

class RecipeTemplate(db.Model):
    __tablename__ = "recipe_templates"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    name = Column(String)
    is_default = Column(Boolean, default=False)
    status = Column(String, default="draft")  # draft, saved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    product = relationship("Product", back_populates="recipe_templates")
    recipe_items = relationship("RecipeItem", back_populates="template")
    production_plans = relationship("ProductionPlan", back_populates="template")

class RecipeItem(db.Model):
    __tablename__ = "recipe_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("recipe_templates.id"))
    material_type_id = Column(Integer, ForeignKey("raw_material_types.id"))
    percentage = Column(Numeric(6, 3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    template = relationship("RecipeTemplate", back_populates="recipe_items")
    material_type = relationship("RawMaterialType", back_populates="recipe_items")

class ProductionPlan(db.Model):
    __tablename__ = "production_plans"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    template_id = Column(Integer, ForeignKey("recipe_templates.id"))
    quantity = Column(Float)
    batch_number = Column(String)
    status = Column(SQLAlchemyEnum(PlanStatus), default=PlanStatus.DRAFT)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    product = relationship("Product", back_populates="production_plans")
    template = relationship("RecipeTemplate", back_populates="production_plans")
    batches = relationship("ProductionBatch", back_populates="plan", cascade="all, delete-orphan")

    def get_progress(self):
        """Возвращает процент выполнения плана"""
        if not self.quantity or self.quantity <= 0:
            return 0
        total_produced = sum([batch.weight for batch in self.batches])
        return (total_produced / self.quantity * 100)
        
    def check_raw_materials_availability(self):
        """Проверяет наличие необходимого количества сырья для выполнения плана
        
        Returns:
            dict: Словарь с информацией о доступности сырья:
                {
                    'available': bool - достаточно ли сырья,
                    'materials': list - список словарей с информацией по каждому виду сырья:
                        [
                            {
                                'name': str - название типа сырья,
                                'needed': float - требуемое количество,
                                'available': float - доступное количество,
                                'sufficient': bool - достаточно ли
                            }
                        ]
                }
        """
        if not self.template:
            return {'available': False, 'materials': []}
            
        result = {
            'available': True,
            'materials': []
        }
        
        # Если нет ингредиентов в рецептуре, считаем что сырья недостаточно
        if not self.template.recipe_items:
            return {'available': False, 'materials': []}
        
        for ingredient in self.template.recipe_items:
            needed_quantity = (self.quantity * ingredient.percentage) / 100
            
            # Получаем все сырье данного типа
            raw_materials = RawMaterial.query.filter_by(type_id=ingredient.material_type_id).all()
            available_quantity = sum(rm.quantity_kg for rm in raw_materials if rm.quantity_kg is not None)
            
            material_info = {
                'name': ingredient.material_type.name,
                'needed': needed_quantity,
                'available': available_quantity,
                'sufficient': available_quantity >= needed_quantity
            }
            
            result['materials'].append(material_info)
            
            if not material_info['sufficient']:
                result['available'] = False
                
        return result

class ProductionBatch(db.Model):
    __tablename__ = "production_batches"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("production_plans.id"))
    batch_number = Column(String)
    weight = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    plan = relationship("ProductionPlan", back_populates="batches")
    materials = relationship("BatchMaterial", back_populates="batch", cascade="all, delete-orphan")

class BatchMaterial(db.Model):
    __tablename__ = "batch_materials"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("production_batches.id"))
    material_batch_id = Column(Integer, ForeignKey("material_batches.id"))
    quantity = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    batch = relationship("ProductionBatch", back_populates="materials")
    material_batch = relationship("MaterialBatch", back_populates="batch_materials") 