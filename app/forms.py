from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SubmitField, SelectField, TextAreaField, DecimalField, PasswordField
from wtforms.validators import DataRequired, NumberRange, ValidationError, Length, Optional, Email
from .models import (
    RawMaterial, RecipeTemplate as Recipe, Product, RawMaterialType, RecipeItem as RecipeIngredient,
    ProductionPlan, PlanStatus, User, UserRole
)

class RawMaterialTypeForm(FlaskForm):
    name = StringField('Название сырья', validators=[DataRequired()])
    submit = SubmitField('Добавить вид сырья')

class RawMaterialForm(FlaskForm):
    type_id = SelectField('Вид сырья', coerce=int, validators=[DataRequired()])
    batch_number = StringField('Номер партии', validators=[DataRequired()])
    quantity_kg = FloatField('Количество (кг)', validators=[DataRequired()])
    date_received = DateField('Дата поступления', format='%Y-%m-%d')
    expiration_date = DateField('Срок годности', format='%Y-%m-%d')
    submit = SubmitField('Добавить партию')

    def __init__(self, *args, **kwargs):
        super(RawMaterialForm, self).__init__(*args, **kwargs)
        self.original_material = kwargs.get('obj')

    def validate_quantity_kg(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError('Количество должно быть положительным числом.')

    def validate_batch_number(self, field):
        if self.type_id.data and self.date_received.data:
            query = RawMaterial.query.filter_by(
                type_id=self.type_id.data,
                batch_number=field.data,
                date_received=self.date_received.data
            )
            if self.original_material:
                query = query.filter(RawMaterial.id != self.original_material.id)
            if query.first():
                raise ValidationError('Партия с таким номером, видом сырья и датой поступления уже существует.')

class ProductForm(FlaskForm):
    name = StringField('Название продукта', validators=[DataRequired()])
    submit = SubmitField('Добавить продукт')

class RecipeForm(FlaskForm):
    name = StringField('Название рецептуры', validators=[DataRequired()])
    product_id = SelectField('Продукт', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Добавить рецептуру')

    def validate_name(self, field):
        if self.product_id.data:
            exists = Recipe.query.filter_by(
                name=field.data, 
                product_id=self.product_id.data,
                status='saved'  # Проверяем только сохраненные рецептуры
            ).first()
            if exists:
                raise ValidationError('Рецептура с таким названием уже существует для выбранного продукта.')

class RecipeIngredientForm(FlaskForm):
    material_type_id = SelectField('Вид сырья', coerce=int, validators=[DataRequired()])
    percentage = DecimalField('Процент', places=3, rounding=None, validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Добавить ингредиент')
    save_recipe = SubmitField('Сохранить рецептуру')

    def validate_material_type_id(self, field):
        if self.recipe and field.data:
            exists = RecipeIngredient.query.filter_by(
                template_id=self.recipe.id,
                material_type_id=field.data
            ).first()
            if exists:
                raise ValidationError('Этот вид сырья уже добавлен в рецептуру.')

class ProductionPlanForm(FlaskForm):
    product_id = SelectField('Продукт', coerce=int, validators=[DataRequired()])
    template_id = SelectField('Рецептура', coerce=int, validators=[DataRequired()])
    batch_number = StringField('Номер партии', validators=[
        DataRequired(),
        Length(min=1, max=50, message='Номер партии должен содержать от 1 до 50 символов')
    ])
    quantity = FloatField('Количество (кг)', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Количество должно быть больше 0')
    ])
    date = DateField('Дата', validators=[Optional()])
    notes = TextAreaField('Примечания', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Сохранить как черновик')
    approve = SubmitField('Утвердить план')

    def validate_template_id(self, field):
        if field.data:
            recipe = Recipe.query.get(field.data)
            if not recipe:
                raise ValidationError('Выбранная рецептура не существует.')
            if recipe.status != 'saved':
                raise ValidationError('Можно использовать только сохраненные рецептуры.')

    def validate_quantity(self, field):
        if field.data and field.data <= 0:
            raise ValidationError('Количество должно быть положительным числом.')
        
        # Проверяем наличие сырья только при утверждении плана
        if self.approve.data and self.template_id.data:
            recipe = Recipe.query.get(self.template_id.data)
            if recipe:
                for ingredient in recipe.recipe_items:
                    needed_quantity = (field.data * float(ingredient.percentage)) / 100
                    available_quantity = sum(
                        rm.quantity_kg for rm in RawMaterial.query.filter_by(type_id=ingredient.material_type_id).all()
                    )
                    if available_quantity < needed_quantity:
                        raise ValidationError(
                            f'Недостаточно сырья {ingredient.material_type.name}. '
                            f'Требуется: {needed_quantity:.2f} кг, доступно: {available_quantity:.2f} кг'
                        )

class ProductionStatusForm(FlaskForm):
    status = SelectField('Статус', validators=[DataRequired()])
    production_date = DateField('Дата производства', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Примечание', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Обновить статус')

    def __init__(self, plan=None, *args, **kwargs):
        super(ProductionStatusForm, self).__init__(*args, **kwargs)
        
        if plan and not plan.template:
            # Для планов с удаленной рецептурой показываем только возможность отмены или перевода в черновик
            self.status.choices = [
                (PlanStatus.DRAFT, PlanStatus.DRAFT.display),
                (PlanStatus.CANCELLED, PlanStatus.CANCELLED.display)
            ]
        else:
            # Для обычных планов показываем все статусы
            self.status.choices = [(status.value, status.display) for status in PlanStatus]
        
        # Если план завершён, блокируем изменение даты производства
        if plan and plan.status == 'завершен':
            self.production_date.render_kw = {'readonly': True, 'disabled': True}

class ProductionBatchForm(FlaskForm):
    batch_number = StringField('Номер замеса', validators=[
        DataRequired(),
        Length(min=1, max=50, message='Номер замеса должен содержать от 1 до 50 символов')
    ])
    quantity = FloatField('Количество (кг)', validators=[
        DataRequired(),
        NumberRange(min=0.01, max=1000, message='Количество должно быть от 0.01 до 1000 кг')
    ])
    submit = SubmitField('Добавить замес')

class BatchIngredientForm(FlaskForm):
    raw_material_id = SelectField('Партия сырья', coerce=int)
    quantity = FloatField('Количество (кг)', validators=[DataRequired()])
    submit = SubmitField('Добавить сырье')

class RawMaterialUsageReportForm(FlaskForm):
    date_from = DateField('С', format='%Y-%m-%d')
    date_to = DateField('По', format='%Y-%m-%d')
    submit = SubmitField('Показать отчет')

class ProductionStatisticsForm(FlaskForm):
    date_from = DateField('С', format='%Y-%m-%d')
    date_to = DateField('По', format='%Y-%m-%d')
    submit = SubmitField('Показать статистику')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class CreateUserForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Имя пользователя должно содержать от 3 до 50 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Введите корректный email адрес')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6, message='Пароль должен содержать минимум 6 символов')
    ])
    role = SelectField('Роль', coerce=str, validators=[DataRequired()])
    submit = SubmitField('Создать пользователя')

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.value, role.value.upper()) for role in UserRole]

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Пользователь с таким именем уже существует.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Пользователь с таким email уже существует.') 