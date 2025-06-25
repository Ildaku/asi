from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from app import app, db
from app.models import (
    RawMaterial, RecipeTemplate as Recipe, Product, RawMaterialType,
    RecipeItem as RecipeIngredient, ProductionPlan, PlanStatus,
    ProductionBatch, MaterialBatch, BatchMaterial, User, UserRole
)
from app.forms import (
    RawMaterialForm, ProductForm, RecipeForm, RecipeIngredientForm,
    RawMaterialTypeForm, ProductionPlanForm, ProductionBatchForm,
    ProductionStatusForm, BatchIngredientForm, RawMaterialUsageReportForm,
    ProductionStatisticsForm, LoginForm
)
from app.utils import (
    create_excel_report, style_header_row, adjust_column_width,
    save_excel_report, format_datetime
)
from sqlalchemy import func, cast, String, text
from sqlalchemy.orm import joinedload
from flask_login import login_user, logout_user, login_required, current_user
from app.decorators import admin_required, operator_required
from flask_migrate import upgrade

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --- Только для ADMIN ---
@app.route('/raw_material_types', methods=['GET', 'POST'])
@admin_required
def raw_material_types():
    form = RawMaterialTypeForm()
    if form.validate_on_submit():
        t = RawMaterialType(name=form.name.data)
        db.session.add(t)
        db.session.commit()
        flash('Вид сырья добавлен!', 'success')
        return redirect(url_for('raw_material_types'))
    types = RawMaterialType.query.all()
    return render_template('raw_material_types.html', form=form, types=types)

@app.route('/raw_material_types/delete/<int:id>', methods=['POST'])
@admin_required
def delete_raw_material_type(id):
    t = RawMaterialType.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Вид сырья удалён!', 'success')
    return redirect(url_for('raw_material_types'))

# --- Сырьё (партии) ---
@app.route('/raw_materials', methods=['GET', 'POST'])
@login_required
def raw_materials():
    form = RawMaterialForm()
    form.type_id.choices = [(t.id, t.name) for t in RawMaterialType.query.all()]
    if form.validate_on_submit():
        # Проверяем права на создание
        if not current_user.is_admin():
            flash('Доступ запрещен. Требуются права администратора для создания.', 'error')
            return redirect(url_for('raw_materials'))
        
        raw = RawMaterial(
            name=form.batch_number.data,
            type_id=form.type_id.data,
            batch_number=form.batch_number.data,
            quantity_kg=form.quantity_kg.data,
            date_received=form.date_received.data or None,
            expiration_date=form.expiration_date.data or None
        )
        db.session.add(raw)
        db.session.commit()
        flash('Партия сырья добавлена!', 'success')
        return redirect(url_for('raw_materials'))
    materials = RawMaterial.query.order_by(RawMaterial.created_at.desc()).all()
    
    # Добавляем информацию о днях до истечения срока годности
    today = datetime.now().date()
    for material in materials:
        if material.expiration_date:
            expiration_date = material.expiration_date.date()
            days_until_expiry = (expiration_date - today).days
            material.days_until_expiry = days_until_expiry
        else:
            material.days_until_expiry = None
    
    return render_template('raw_materials.html', form=form, materials=materials)

@app.route('/raw_materials/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_raw_material(id):
    material = RawMaterial.query.get_or_404(id)
    form = RawMaterialForm(obj=material)
    form.type_id.choices = [(t.id, t.name) for t in RawMaterialType.query.all()]
    if form.validate_on_submit():
        # Сохраняем старое количество для логирования изменений
        old_quantity = material.quantity_kg
        new_quantity = form.quantity_kg.data
        
        material.type_id = form.type_id.data
        material.batch_number = form.batch_number.data
        material.quantity_kg = new_quantity
        material.date_received = form.date_received.data or material.date_received
        material.expiration_date = form.expiration_date.data or material.expiration_date
        
        db.session.commit()
        
        # Показываем информацию об изменении количества
        if old_quantity != new_quantity:
            change = new_quantity - old_quantity
            if change > 0:
                flash(f'Партия сырья обновлена! Количество увеличено на {change:.2f} кг (с {old_quantity:.2f} до {new_quantity:.2f} кг)', 'success')
            else:
                flash(f'Партия сырья обновлена! Количество уменьшено на {abs(change):.2f} кг (с {old_quantity:.2f} до {new_quantity:.2f} кг)', 'success')
        else:
            flash('Партия сырья обновлена!', 'success')
            
        return redirect(url_for('raw_materials'))
    return render_template('edit_raw_material.html', form=form, material=material)

@app.route('/raw_materials/delete/<int:id>', methods=['POST'])
@admin_required
def delete_raw_material(id):
    material = RawMaterial.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    flash('Партия сырья удалена!', 'success')
    return redirect(url_for('raw_materials'))

# --- Продукты ---
@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    form = ProductForm()
    if form.validate_on_submit():
        # Проверяем права на создание
        if not current_user.is_admin():
            flash('Доступ запрещен. Требуются права администратора для создания.', 'error')
            return redirect(url_for('products'))
        
        product = Product(name=form.name.data)
        db.session.add(product)
        db.session.commit()
        flash('Продукт добавлен!', 'success')
        return redirect(url_for('products'))
    products = Product.query.all()
    return render_template('products.html', form=form, products=products)

@app.route('/products/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # Проверяем, есть ли связанные рецептуры
    if product.recipe_templates:
        flash('Невозможно удалить продукт, так как для него существуют рецептуры.', 'error')
        return redirect(url_for('products'))
    
    # Проверяем, есть ли связанные планы производства
    if product.production_plans:
        flash('Невозможно удалить продукт, так как для него существуют планы производства.', 'error')
        return redirect(url_for('products'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Продукт удален!', 'success')
    return redirect(url_for('products'))

# --- Рецептуры ---
@app.route('/recipes', methods=['GET', 'POST'])
@login_required
def recipes():
    form = RecipeForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    if form.validate_on_submit():
        # Проверяем права на создание
        if not current_user.is_admin():
            flash('Доступ запрещен. Требуются права администратора для создания.', 'error')
            return redirect(url_for('recipes'))
        
        recipe = Recipe(
            name=form.name.data, 
            product_id=form.product_id.data,
            status='draft'
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Рецептура создана! Теперь добавьте ингредиенты.', 'success')
        return redirect(url_for('recipe_ingredients', recipe_id=recipe.id))
    recipes = Recipe.query.filter_by(status='saved').all()  # Показываем только сохраненные
    drafts = Recipe.query.filter_by(status='draft').all()  # Отдельно показываем черновики
    return render_template('recipes.html', form=form, recipes=recipes, drafts=drafts)

@app.route('/recipes/delete/<int:id>', methods=['POST'])
@admin_required
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    
    # Проверяем, используется ли рецептура в планах производства
    plans_using_recipe = ProductionPlan.query.filter_by(template_id=recipe.id).all()
    if plans_using_recipe:
        plan_numbers = [str(plan.id) for plan in plans_using_recipe]
        flash(f'Невозможно удалить рецептуру, так как она используется в планах производства: {", ".join(plan_numbers)}', 'error')
        return redirect(url_for('recipes'))
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Рецептура удалена!', 'success')
    return redirect(url_for('recipes'))

# --- Ингредиенты рецептуры ---
@app.route('/recipes/<int:recipe_id>/ingredients', methods=['GET', 'POST'])
@login_required
def recipe_ingredients(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Для сохраненных рецептур запрещаем только модификации
    if recipe.status == 'saved' and request.method == 'POST':
        flash('Эта рецептура уже сохранена и не может быть изменена.', 'warning')
        return redirect(url_for('recipe_ingredients', recipe_id=recipe_id))
        
    form = RecipeIngredientForm()
    form.recipe = recipe  # для валидации
    
    # Получаем список типов сырья
    raw_material_types = RawMaterialType.query.all()
    form.material_type_id.choices = [(rmt.id, rmt.name) for rmt in raw_material_types]
    
    if request.method == 'POST':
        # Проверяем права на модификацию
        if not current_user.is_admin():
            flash('Доступ запрещен. Требуются права администратора для изменения рецептуры.', 'error')
            return redirect(url_for('recipe_ingredients', recipe_id=recipe_id))
        
        if 'save_recipe' in request.form:  # Нажата кнопка "Сохранить рецептуру"
            total_percent = sum(item.percentage for item in recipe.recipe_items)
            if not recipe.recipe_items:
                flash('Добавьте хотя бы один ингредиент перед сохранением рецептуры.', 'error')
            elif abs(total_percent - 100) > 0.01:  # Учитываем возможную погрешность float
                flash(f'Сумма процентов должна быть равна 100%. Текущая сумма: {total_percent}%', 'error')
            else:
                recipe.status = 'saved'
                db.session.commit()
                flash('Рецептура успешно сохранена!', 'success')
                return redirect(url_for('recipes'))
        elif form.validate():  # Нажата кнопка "Добавить ингредиент"
            # Проверяем, не добавлен ли уже этот тип сырья
            existing = RecipeIngredient.query.filter_by(
                template_id=recipe.id,
                material_type_id=form.material_type_id.data
            ).first()
            
            if existing:
                flash('Этот вид сырья уже добавлен в рецептуру.', 'error')
            else:
                ingredient = RecipeIngredient(
                    template_id=recipe.id,
                    material_type_id=form.material_type_id.data,
                    percentage=form.percentage.data
                )
                db.session.add(ingredient)
                db.session.commit()
                flash('Ингредиент добавлен!', 'success')
                
                # Показываем текущую сумму процентов
                total_percent = sum(item.percentage for item in recipe.recipe_items)
                if total_percent > 100:
                    flash(f'Предупреждение: сумма процентов превышает 100% ({total_percent}%)', 'warning')
                elif total_percent < 100:
                    flash(f'Осталось добавить {100 - total_percent}%', 'info')
            
        return redirect(url_for('recipe_ingredients', recipe_id=recipe.id))
        
    ingredients = RecipeIngredient.query.filter_by(template_id=recipe.id).all()
    total_percent = sum(item.percentage for item in ingredients)
    return render_template(
        'recipe_ingredients.html',
        form=form if recipe.status != 'saved' else None,  # Не показываем форму для сохраненных рецептур
        recipe=recipe,
        ingredients=ingredients,
        total_percent=total_percent
    )

@app.route('/recipes/<int:recipe_id>/ingredients/<int:ingredient_id>/delete', methods=['POST'])
@admin_required
def delete_recipe_ingredient(recipe_id, ingredient_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.status == 'saved':
        flash('Нельзя изменять сохраненную рецептуру.', 'error')
        return redirect(url_for('recipes'))
        
    ingredient = RecipeIngredient.query.get_or_404(ingredient_id)
    if ingredient.template_id != recipe_id:
        flash('Ошибка: ингредиент не принадлежит указанной рецептуре.', 'error')
        return redirect(url_for('recipes'))
        
    db.session.delete(ingredient)
    db.session.commit()
    flash('Ингредиент удален из рецептуры!', 'success')
    return redirect(url_for('recipe_ingredients', recipe_id=recipe_id))

@app.route('/production_plans')
@login_required
def production_plans():
    # Получаем параметры фильтрации
    product_id = request.args.get('product_id', type=int)
    status = request.args.get('status')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')

    query = ProductionPlan.query

    # Применяем фильтры
    if product_id:
        query = query.filter(ProductionPlan.product_id == product_id)
    if status:
        query = query.filter(ProductionPlan.status == status)
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(ProductionPlan.created_at >= date_from)
        except ValueError:
            flash('Неверный формат даты начала периода.', 'error')
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            # Включаем весь день до 23:59:59
            query = query.filter(ProductionPlan.created_at <= date_to + timedelta(days=1, seconds=-1))
        except ValueError:
            flash('Неверный формат даты конца периода.', 'error')

    # Сортировка
    plans = query.order_by(ProductionPlan.created_at.desc()).all()

    # Данные для форм фильтров
    products = Product.query.order_by(Product.name).all()

    # Цвета для статусов
    status_colors = {
        PlanStatus.DRAFT: 'secondary',
        PlanStatus.APPROVED: 'info',
        PlanStatus.IN_PROGRESS: 'primary',
        PlanStatus.COMPLETED: 'success',
        PlanStatus.CANCELLED: 'danger'
    }

    return render_template(
        'production_plans.html',
        plans=plans,
        products=products,
        status_colors=status_colors,
        PlanStatus=PlanStatus
    )

@app.route('/production_plans/<int:plan_id>/update_status', methods=['POST'])
@operator_required
def update_plan_status(plan_id):
    plan = ProductionPlan.query.get_or_404(plan_id)
    form = ProductionStatusForm(plan=plan)
    
    if form.validate_on_submit():
        old_status = plan.status
        new_status = form.status.data

        # Проверка перед установкой статуса "завершен"
        if new_status == PlanStatus.COMPLETED:
            total_produced = sum(batch.weight for batch in plan.batches)
            # Сравниваем с небольшой погрешностью для чисел с плавающей точкой
            if total_produced < plan.quantity * 0.999:
                flash(f'Невозможно завершить план. Произведено {total_produced:.2f} кг из {plan.quantity:.2f} кг.', 'error')
                return redirect(url_for('production_plan_detail', plan_id=plan.id))
            # Строгая проверка внесения всех ингредиентов
            for batch in plan.batches:
                for recipe_item in plan.template.recipe_items:
                    need_qty = batch.weight * recipe_item.percentage / 100
                    added_qty = sum(
                        bi.quantity for bi in batch.materials
                        if bi.material_batch.material.type_id == recipe_item.material_type_id
                    )
                    if abs(added_qty - need_qty) > 0.01:  # допускаем небольшую погрешность
                        flash(
                            f'Невозможно завершить план. В замесе №{batch.batch_number} для ингредиента "{recipe_item.material_type.name}" внесено {added_qty:.2f} кг из {need_qty:.2f} кг.',
                            'error'
                        )
                        return redirect(url_for('production_plan_detail', plan_id=plan.id))
        
        # Обработка старого формата статуса (без ё)
        old_status_normalized = old_status.replace("утвержден", "утверждён")
        
        # Получаем отображаемые значения статусов, с защитой от отсутствующих ключей
        old_status_display = old_status_normalized
        new_status_display = new_status
        
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
        status_note = f"[{timestamp}] Статус изменен: {old_status_display} → {new_status_display}"
        
        # Добавляем примечание к существующим
        if plan.notes:
            plan.notes = status_note + "\n" + plan.notes
        else:
            plan.notes = status_note
            
        if form.notes.data:
            plan.notes = form.notes.data + "\n" + plan.notes
        
        plan.status = new_status
        db.session.commit()
        
        flash('Статус успешно обновлен!', 'success')
        return redirect(url_for('production_plan_detail', plan_id=plan.id))
    
    return redirect(url_for('production_plan_detail', plan_id=plan.id))

@app.route('/production_plans/<int:plan_id>/add_batch', methods=['POST'])
@operator_required
def add_batch(plan_id):
    plan = ProductionPlan.query.get_or_404(plan_id)
    form = ProductionBatchForm()
    
    if form.validate_on_submit():
        # Проверяем максимальный вес замеса
        if form.quantity.data > 1000:
            flash('Вес замеса не может превышать 1000 кг', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        # Проверяем уникальность номера замеса в рамках текущего плана
        existing_batch = ProductionBatch.query.filter_by(
            plan_id=plan.id,
            batch_number=form.batch_number.data
        ).first()
        if existing_batch:
            flash('Замес с таким номером уже существует в текущем плане', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        # Проверяем, не превышает ли общее количество план
        total_quantity = sum([batch.weight for batch in plan.batches]) + form.quantity.data
        if total_quantity > plan.quantity:
            flash(f'Общее количество замесов ({total_quantity} кг) превышает план ({plan.quantity} кг)', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        batch = ProductionBatch(
            plan=plan,
            batch_number=form.batch_number.data,
            weight=form.quantity.data
        )
        db.session.add(batch)
        
        # Добавляем запись в примечания
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
        batch_note = f"[{timestamp}] Добавлен замес №{batch.batch_number} ({batch.weight} кг)"
        
        if plan.notes:
            plan.notes = batch_note + "\n\n" + plan.notes
        else:
            plan.notes = batch_note
            
        db.session.commit()
        flash('Замес добавлен', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Ошибка в поле {getattr(form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('production_plan_detail', plan_id=plan_id))

@app.route('/production_plans/<int:plan_id>/add_batch_ingredient', methods=['POST'])
@operator_required
def add_batch_ingredient(plan_id):
    form = BatchIngredientForm()
    
    # Получаем замес и его тип сырья
    batch_id = request.form.get('batch_id')
    if not batch_id:
        flash('Не указан ID замеса', 'error')
        return redirect(url_for('production_plan_detail', plan_id=plan_id))
    
    batch = ProductionBatch.query.get_or_404(batch_id)
    
    # Проверяем статус плана
    if batch.plan.status not in [PlanStatus.IN_PROGRESS, PlanStatus.APPROVED]:
        flash('Нельзя добавлять ингредиенты в этом статусе', 'error')
        return redirect(url_for('production_plan_detail', plan_id=plan_id))
    
    # Находим тип сырья для текущего ингредиента
    ingredient_info = None
    for info in batch.plan.template.recipe_items:
        added_qty = sum([
            bi.quantity for bi in batch.materials
            if bi.material_batch.material.type_id == info.material_type_id
        ])
        if (batch.weight * info.percentage / 100) > added_qty:
            ingredient_info = info
            break
    
    if not ingredient_info:
        flash('Все ингредиенты уже добавлены', 'info')
        return redirect(url_for('production_plan_detail', plan_id=plan_id))
    
    # Получаем доступное сырье для данного типа
    available_materials = RawMaterial.query.filter_by(type_id=ingredient_info.material_type_id).all()
    form.raw_material_id.choices = [(m.id, f"{m.batch_number} ({m.quantity_kg} кг)") for m in available_materials]
    
    if form.validate_on_submit():
        # Проверяем, что выбранное сырье подходит по типу
        raw_material = RawMaterial.query.get(form.raw_material_id.data)
        if not raw_material or raw_material.type_id != ingredient_info.material_type_id:
            flash('Выбрано неверное сырье', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        # Проверяем количество
        need_qty = (batch.weight * ingredient_info.percentage / 100) - sum([
            bi.quantity for bi in batch.materials
            if bi.material_batch.material.type_id == ingredient_info.material_type_id
        ])
        
        if form.quantity.data > need_qty:
            flash(f'Нельзя добавить больше чем нужно ({need_qty:.2f} кг)', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        if form.quantity.data > raw_material.quantity_kg:
            flash(f'Недостаточно сырья (доступно {raw_material.quantity_kg:.2f} кг)', 'error')
            return redirect(url_for('production_plan_detail', plan_id=plan_id))
        
        # Создаем партию материала
        material_batch = MaterialBatch(
            material=raw_material,
            batch_number=raw_material.batch_number,
            quantity=form.quantity.data,
            remaining_quantity=form.quantity.data
        )
        db.session.add(material_batch)
        db.session.flush()  # Получаем ID созданной партии
        
        # Добавляем ингредиент
        ingredient = BatchMaterial(
            batch=batch,
            material_batch=material_batch,
            quantity=form.quantity.data
        )
        
        # Уменьшаем количество доступного сырья
        raw_material.quantity_kg -= form.quantity.data
        
        db.session.add(ingredient)
        db.session.commit()
        
        flash('Ингредиент добавлен!', 'success')
        return redirect(url_for('production_plan_detail', plan_id=plan_id))
    
    return redirect(url_for('production_plan_detail', plan_id=plan_id))

@app.route('/production_plans/<int:plan_id>')
@login_required
def production_plan_detail(plan_id):
    plan = ProductionPlan.query.get_or_404(plan_id)
    
    # Проверяем существование рецептуры
    if not plan.template:
        flash('Рецептура для данного плана была удалена. Измените статус плана на "черновик" или "отменён", чтобы удалить его.', 'warning')
    
    # Вычисляем прогресс производства
    total_produced = sum([batch.weight for batch in plan.batches])
    progress_percent = (total_produced / plan.quantity * 100) if plan.quantity > 0 else 0
    
    # Проверяем наличие сырья только если есть рецептура
    raw_materials_availability = {}
    can_start = True
    start_message = ""
    
    if plan.template:
        for ingredient in plan.template.recipe_items:
            type_id = ingredient.material_type_id
            needed_qty = (plan.quantity * ingredient.percentage / 100)
            available_qty = sum([rm.quantity_kg for rm in RawMaterial.query.filter_by(type_id=type_id).all()])
            
            raw_materials_availability[type_id] = {
                'type': ingredient.material_type,
                'quantity_needed': needed_qty,
                'quantity_available': available_qty,
                'is_available': available_qty >= needed_qty,
                'shortage': max(0, needed_qty - available_qty)
            }
            
            if available_qty < needed_qty:
                can_start = False
                start_message = "Недостаточно сырья для начала производства"

    # Цвета для статусов
    status_colors = {
        PlanStatus.DRAFT: 'secondary',
        PlanStatus.APPROVED: 'info',
        PlanStatus.IN_PROGRESS: 'primary',
        PlanStatus.COMPLETED: 'success',
        PlanStatus.CANCELLED: 'danger'
    }

    # Информация о замесах
    batches_info = []
    if plan.template:
        for batch in plan.batches:
            ingredients_info = []
            for recipe_ingredient in plan.template.recipe_items:
                type_id = recipe_ingredient.material_type_id
                need_qty = batch.weight * recipe_ingredient.percentage / 100
                batch_ingredients_query = BatchMaterial.query.filter_by(batch_id=batch.id)
                batch_ingredients = [
                    bi for bi in batch_ingredients_query.all()
                    if bi.material_batch.material.type_id == type_id
                ]
                added_qty = sum(bi.quantity for bi in batch_ingredients)

                # Группируем партии по batch_number
                grouped_batches = {}
                for bi in batch_ingredients:
                    key = bi.material_batch.batch_number
                    if key not in grouped_batches:
                        grouped_batches[key] = {
                            'batch_number': bi.material_batch.batch_number,
                            'material_name': bi.material_batch.material.name,
                            'quantity': 0.0
                        }
                    grouped_batches[key]['quantity'] += bi.quantity

                ingredients_info.append({
                    'type': recipe_ingredient.material_type,
                    'need_qty': need_qty,
                    'added_qty': added_qty,
                    'to_add_qty': max(0, need_qty - added_qty),
                    'added_materials': list(grouped_batches.values()),
                    'original_batch_materials': batch_ingredients
                })
            
            batches_info.append({
                'batch': batch,
                'ingredients': ingredients_info
            })

    # Создаем формы
    status_form = ProductionStatusForm(plan=plan)
    status_form.status.data = plan.status  # Устанавливаем текущий статус
    batch_form = ProductionBatchForm()
    batch_ingredient_form = BatchIngredientForm()

    return render_template(
        'production_plan_detail.html',
        plan=plan,
        raw_materials_availability=raw_materials_availability,
        can_start=can_start,
        start_message=start_message,
        progress_percent=progress_percent,
        total_produced=total_produced,
        status_colors=status_colors,
        batches_info=batches_info,
        status_form=status_form,
        batch_form=batch_form,
        batch_ingredient_form=batch_ingredient_form,
        PlanStatus=PlanStatus)

@app.route('/batches/delete/<int:batch_id>', methods=['POST'])
@login_required
def delete_batch(batch_id):
    batch = ProductionBatch.query.get_or_404(batch_id)
    plan = batch.plan
    if plan.status == 'completed':
        flash('Нельзя удалять замес после завершения плана!', 'danger')
        return redirect(url_for('production_plan_detail', plan_id=plan.id))
    db.session.delete(batch)
    db.session.commit()
    flash('Замес удалён!', 'success')
    return redirect(url_for('production_plan_detail', plan_id=plan.id))

@app.route('/batch_ingredients/delete/<int:ingredient_id>', methods=['POST'])
@login_required
def delete_batch_ingredient(ingredient_id):
    # Находим ингредиент, который нужно удалить
    ingredient = BatchMaterial.query.get_or_404(ingredient_id)
    plan_id = ingredient.batch.plan_id

    # Проверяем статус плана, чтобы запретить изменения в завершенных планах
    if ingredient.batch.plan.status == PlanStatus.COMPLETED:
        flash('Нельзя удалять ингредиенты из завершенного плана!', 'danger')
        return redirect(url_for('production_plan_detail', plan_id=plan_id))

    try:
        # Возвращаем количество на склад
        # Находим партию сырья, из которой был взят этот ингредиент
        material_batch = ingredient.material_batch
        if material_batch and material_batch.material:
            material_batch.material.quantity_kg += ingredient.quantity
        
        # Удаляем запись об использовании ингредиента
        db.session.delete(ingredient)
        db.session.commit()
        flash('Ингредиент удален из замеса!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении ингредиента: {str(e)}', 'error')
        
    return redirect(url_for('production_plan_detail', plan_id=plan_id))

@app.route('/reports')
@login_required
def reports():
    # Остатки сырья
    raw_materials = RawMaterial.query.order_by(RawMaterial.type_id, RawMaterial.batch_number).all()
    # История производства
    plans = ProductionPlan.query.order_by(ProductionPlan.created_at.desc()).all()
    return render_template('reports.html', raw_materials=raw_materials, plans=plans)

@app.route('/recipes/by_product/<int:product_id>')
@login_required
def recipes_by_product(product_id):
    recipes = Recipe.query.filter_by(
        product_id=product_id,
        status='saved'
    ).all()
    return jsonify([{
        'id': recipe.id,
        'name': recipe.name
    } for recipe in recipes])

@app.route('/raw_materials/by_type/<int:type_id>')
@login_required
def raw_materials_by_type(type_id):
    materials = RawMaterial.query.filter_by(type_id=type_id).all()
    return jsonify([{
        'id': m.id,
        'type_name': m.material_type.name,
        'batch_number': m.batch_number,
        'quantity_kg': m.quantity_kg
    } for m in materials])

@app.route('/raw_materials/available/<int:type_id>')
@login_required
def get_available_raw_materials(type_id):
    materials = RawMaterial.query.filter_by(type_id=type_id).all()
    return jsonify([{
        'id': m.id,
        'name': f"{m.batch_number} ({m.quantity_kg:.2f} кг)"
    } for m in materials if m.quantity_kg > 0])

@app.route('/production_plans/create', methods=['GET', 'POST'])
@admin_required
def create_production_plan():
    form = ProductionPlanForm()
    
    # Заполняем список продуктов
    products = Product.query.order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    # Заполняем список рецептур для выбранного продукта
    if request.method == 'POST':
        selected_product_id = int(request.form.get('product_id', 0))
    else:
        selected_product_id = request.args.get('product_id', type=int)
        if not selected_product_id and products:
            selected_product_id = products[0].id
    
    if selected_product_id:
        recipes = Recipe.query.filter_by(
            product_id=selected_product_id,
            status='saved'
        ).order_by(Recipe.name).all()
        form.template_id.choices = [(r.id, r.name) for r in recipes]
    else:
        form.template_id.choices = []
    
    if form.validate_on_submit():
        plan = ProductionPlan(
            product_id=form.product_id.data,
            template_id=form.template_id.data,
            batch_number=form.batch_number.data,
            quantity=form.quantity.data,
            notes=form.notes.data,
            status=PlanStatus.DRAFT
        )
        
        # Если нажата кнопка "Утвердить"
        if form.approve.data:
            # Проверка наличия сырья уже выполнена в validate_quantity
            plan.status = PlanStatus.APPROVED
            flash('План производства создан и утверждён!', 'success')
        else:
            flash('План производства создан как черновик', 'success')
        
        db.session.add(plan)
        try:
            db.session.commit()
            return redirect(url_for('production_plan_detail', plan_id=plan.id))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint' in str(e):
                flash('План производства с таким номером партии уже существует', 'error')
            else:
                flash('Произошла ошибка при сохранении плана', 'error')
            return redirect(url_for('create_production_plan'))
    
    return render_template('create_production_plan.html',
                         form=form,
                         selected_product_id=selected_product_id)

@app.route('/production_plans/<int:plan_id>/delete', methods=['POST'])
@admin_required
def delete_production_plan(plan_id):
    plan = ProductionPlan.query.get_or_404(plan_id)
    
    # Проверяем, можно ли удалить план
    if plan.status not in [PlanStatus.DRAFT, PlanStatus.CANCELLED]:
        flash('Можно удалить только черновик плана производства или отмененный план', 'error')
        return redirect(url_for('production_plans'))
    
    # Получаем номер партии для сообщения
    batch_number = plan.batch_number or f'#{plan.id}'
    
    try:
        # Удаляем все замесы и их ингредиенты
        for batch in plan.batches:
            db.session.delete(batch)
        
        # Удаляем сам план
        db.session.delete(plan)
        db.session.commit()
        
        flash(f'План производства {batch_number} удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении плана производства: {str(e)}', 'error')
    
    return redirect(url_for('production_plans'))

@app.route('/reports/raw_material_usage', methods=['GET', 'POST'])
@login_required
def raw_material_usage_report():
    form = RawMaterialUsageReportForm()
    usage_data = None

    if form.validate_on_submit():
        date_from = form.date_from.data
        date_to = form.date_to.data

        query = (
            db.session.query(
                RawMaterialType.name.label('type_name'),
                MaterialBatch.batch_number,
                db.func.sum(BatchMaterial.quantity).label('used_qty')
            )
            .join(MaterialBatch, MaterialBatch.id == BatchMaterial.material_batch_id)
            .join(RawMaterial, RawMaterial.id == MaterialBatch.material_id)
            .join(RawMaterialType, RawMaterialType.id == RawMaterial.type_id)
            .join(ProductionBatch, ProductionBatch.id == BatchMaterial.batch_id)
            .join(ProductionPlan, ProductionPlan.id == ProductionBatch.plan_id)
            .filter(BatchMaterial.quantity > 0)
        )
        if date_from:
            query = query.filter(ProductionPlan.created_at >= date_from)
        if date_to:
            query = query.filter(ProductionPlan.created_at <= date_to)
        query = query.group_by(RawMaterialType.name, MaterialBatch.batch_number)
        usage_data = query.all()
    else:
        usage_data = None

    return render_template(
        'raw_material_usage_report.html',
        form=form,
        usage_data=usage_data
    )

@app.route('/reports/production_statistics', methods=['GET', 'POST'])
@login_required
def production_statistics():
    form = ProductionStatisticsForm()
    statistics_data = None
    totals = {}

    if form.validate_on_submit():
        date_from = form.date_from.data
        date_to = form.date_to.data

        query = (
            ProductionPlan.query
            .options(
                joinedload(ProductionPlan.batches)
                .joinedload(ProductionBatch.materials)
                .joinedload(BatchMaterial.material_batch)
                .joinedload(MaterialBatch.material)
                .joinedload(RawMaterial.type)
            )
            .join(Product, Product.id == ProductionPlan.product_id)
            .join(Recipe, Recipe.id == ProductionPlan.template_id)
            .filter(ProductionPlan.status == PlanStatus.COMPLETED)
        )

        if date_from:
            query = query.filter(ProductionPlan.created_at >= date_from)
        if date_to:
            date_to_end_of_day = date_to + timedelta(days=1, seconds=-1)
            query = query.filter(ProductionPlan.created_at <= date_to_end_of_day)

        # Сортировка по дате и продукту
        statistics_data = query.order_by(Product.name, ProductionPlan.created_at).all()
        
        # Подготовим итоговые данные по продуктам
        if statistics_data:
            for plan in statistics_data:
                key = (plan.product.name, plan.template.name)
                if key not in totals:
                    totals[key] = {
                        'product_name': plan.product.name,
                        'recipe_name': plan.template.name,
                        'total_quantity': 0,
                        'plans_count': 0
                    }
                totals[key]['total_quantity'] += plan.quantity
                totals[key]['plans_count'] += 1

    return render_template(
        'production_statistics.html',
        form=form,
        statistics_data=statistics_data,
        totals=totals if statistics_data else None
    )

@app.route('/reports/raw_material_forecast', methods=['GET'])
@login_required
def raw_material_forecast():
    # Получаем все утвержденные планы производства
    approved_plans = ProductionPlan.query.filter_by(status=PlanStatus.APPROVED).order_by(ProductionPlan.created_at).all()
    
    # Получаем текущие остатки сырья
    current_stock = {}
    for material in RawMaterial.query.all():
        if material.type_id not in current_stock:
            current_stock[material.type_id] = 0
        current_stock[material.type_id] += material.quantity_kg

    # Прогноз потребности по дням
    forecast = {}
    raw_material_types = RawMaterialType.query.all()
    
    for plan in approved_plans:
        date_str = plan.created_at.strftime('%Y-%m-%d')
        if date_str not in forecast:
            forecast[date_str] = {t.id: 0 for t in raw_material_types}
            
        # Для каждого замеса в плане
        plan_quantity = plan.quantity
        recipe = plan.template
        
        # Рассчитываем потребность в сырье для каждого типа
        for ingredient in recipe.recipe_items:
            needed_kg = (ingredient.percentage / 100) * plan_quantity
            forecast[date_str][ingredient.material_type_id] += needed_kg
    
    # Сортируем даты
    sorted_dates = sorted(forecast.keys())
    
    # Рассчитываем накопительный расход и сравниваем с остатками
    cumulative_usage = {t.id: 0 for t in raw_material_types}
    for date in sorted_dates:
        for type_id in forecast[date]:
            cumulative_usage[type_id] += forecast[date][type_id]
    
    return render_template(
        'raw_material_forecast.html',
        forecast=forecast,
        sorted_dates=sorted_dates,
        raw_material_types=raw_material_types,
        current_stock=current_stock,
        cumulative_usage=cumulative_usage
    )

@app.route('/reports/raw_material_usage/export')
@login_required
def export_raw_material_usage():
    wb, output = create_excel_report()
    
    # Создаем лист для отчета
    ws = wb.create_sheet("Использование сырья")
    
    # Заголовки
    headers = ["Дата", "Вид сырья", "Партия", "Использовано (кг)", "План производства", "Продукт"]
    ws.append(headers)
    style_header_row(ws)
    
    # Получаем данные
    usage_data = []
    plans = ProductionPlan.query.order_by(ProductionPlan.created_at.desc()).all()
    
    for plan in plans:
        for batch in plan.batches:
            for ingredient in batch.materials:
                usage_data.append([
                    plan.created_at.strftime("%Y-%m-%d"),
                    ingredient.material_batch.material.type.name,
                    ingredient.material_batch.material.batch_number,
                    ingredient.quantity,
                    f"№{plan.batch_number}",
                    plan.product.name
                ])
    
    # Добавляем данные
    for row in usage_data:
        ws.append(row)
    
    # Форматирование
    adjust_column_width(ws)
    
    # Сохраняем и отправляем файл
    output = save_excel_report(wb, output)
    filename = f"raw_material_usage_{format_datetime(datetime.now())}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/reports/production_statistics/export')
@login_required
def export_production_statistics():
    wb, output = create_excel_report()
    
    # Создаем лист для отчета
    ws = wb.create_sheet("Детализация производства")
    
    # Заголовки
    headers = [
        "Дата плана", "Продукт", "Рецептура", "План №", "Статус плана", "Плановое кол-во (кг)",
        "Замес №", "Вес замеса (кг)",
        "Сырье", "Партия сырья", "Кол-во сырья (кг)"
    ]
    ws.append(headers)
    style_header_row(ws)
    
    # Получаем все данные одним запросом для эффективности
    plans = ProductionPlan.query.options(
        joinedload(ProductionPlan.product),
        joinedload(ProductionPlan.template),
        joinedload(ProductionPlan.batches).options(
            joinedload(ProductionBatch.materials).options(
                joinedload(BatchMaterial.material_batch).options(
                    joinedload(MaterialBatch.material).options(
                        joinedload(RawMaterial.type)
                    )
                )
            )
        )
    ).order_by(ProductionPlan.created_at.desc()).all()
    
    # Заполняем лист данными
    for plan in plans:
        plan_info = [
            plan.created_at.strftime("%Y-%m-%d"),
            plan.product.name,
            plan.template.name,
            plan.batch_number,
            plan.status,
            plan.quantity
        ]
        
        if not plan.batches:
            ws.append(plan_info) # Добавляем только информацию о плане, если нет замесов
        else:
            for batch in plan.batches:
                batch_info = plan_info + [
                    batch.batch_number,
                    batch.weight
                ]
                if not batch.materials:
                    ws.append(batch_info) # Добавляем инфо о плане и замесе, если нет ингредиентов
                else:
                    for material in batch.materials:
                        material_info = batch_info + [
                            material.material_batch.material.type.name,
                            material.material_batch.batch_number,
                            material.quantity
                        ]
                        ws.append(material_info)
                        
    adjust_column_width(ws)
    
    # Удаляем стандартный пустой лист, создаваемый библиотекой
    if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
        del wb["Sheet"]

    # Сохраняем и отправляем файл
    output = save_excel_report(wb, output)
    filename = f"production_statistics_{format_datetime(datetime.now())}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/reports/raw_material_forecast/export')
@login_required
def export_raw_material_forecast():
    wb, output = create_excel_report()
    
    # Текущие остатки
    ws_stock = wb.create_sheet("Текущие остатки")
    headers_stock = ["Вид сырья", "Остаток (кг)"]
    ws_stock.append(headers_stock)
    style_header_row(ws_stock)
    
    current_stock = {}
    for material in RawMaterial.query.all():
        if material.type_id not in current_stock:
            current_stock[material.type_id] = 0
        current_stock[material.type_id] += material.quantity_kg
    
    for type in RawMaterialType.query.all():
        ws_stock.append([
            type.name,
            current_stock.get(type.id, 0)
        ])
    
    adjust_column_width(ws_stock)
    
    # Прогноз по дням
    ws_forecast = wb.create_sheet("Прогноз по дням")
    raw_material_types = RawMaterialType.query.all()
    
    # Заголовки для прогноза
    headers_forecast = ["Дата"] + [t.name for t in raw_material_types]
    ws_forecast.append(headers_forecast)
    style_header_row(ws_forecast)
    
    # Получаем прогноз
    forecast = {}
    approved_plans = ProductionPlan.query.filter_by(status=PlanStatus.APPROVED).order_by(ProductionPlan.created_at).all()
    
    for plan in approved_plans:
        date_str = plan.created_at.strftime('%Y-%m-%d')
        if date_str not in forecast:
            forecast[date_str] = {t.id: 0 for t in raw_material_types}
        
        plan_quantity = plan.quantity
        recipe = plan.template
        
        for ingredient in recipe.recipe_items:
            needed_kg = (ingredient.percentage / 100) * plan_quantity
            forecast[date_str][ingredient.material_type_id] += needed_kg
    
    # Добавляем данные прогноза
    for date in sorted(forecast.keys()):
        row = [date] + [forecast[date][t.id] for t in raw_material_types]
        ws_forecast.append(row)
    
    # Добавляем итоговую строку
    total_row = ["Общая потребность"]
    for type in raw_material_types:
        total = sum(forecast[date][type.id] for date in forecast)
        total_row.append(total)
    ws_forecast.append([])  # Пустая строка перед итогами
    ws_forecast.append(total_row)
    
    adjust_column_width(ws_forecast)
    
    # Анализ достаточности
    ws_analysis = wb.create_sheet("Анализ достаточности")
    headers_analysis = ["Вид сырья", "Текущий остаток (кг)", "Общая потребность (кг)", "Баланс (кг)", "Статус"]
    ws_analysis.append(headers_analysis)
    style_header_row(ws_analysis)
    
    for type in raw_material_types:
        total_needed = sum(forecast[date][type.id] for date in forecast) if forecast else 0
        current = current_stock.get(type.id, 0)
        balance = current - total_needed
        status = "Достаточно" if balance >= 0 else f"Требуется докупить {abs(balance):.2f} кг"
        
        ws_analysis.append([
            type.name,
            current,
            total_needed,
            balance,
            status
        ])
    
    adjust_column_width(ws_analysis)
    
    # Сохраняем и отправляем файл
    output = save_excel_report(wb, output)
    filename = f"raw_material_forecast_{format_datetime(datetime.now())}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        from app.models import User
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# Временный маршрут для создания пользователей admin и operator
@app.route('/create_default_users')
def create_default_users():
    created = []
    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role=UserRole.ADMIN
        )
        admin.set_password('admin123')  # Пароль для admin
        db.session.add(admin)
        created.append('admin')
    # Operator
    if not User.query.filter_by(username='operator').first():
        operator = User(
            username='operator',
            email='operator@example.com',
            role=UserRole.OPERATOR
        )
        operator.set_password('operator123')  # Пароль для operator
        db.session.add(operator)
        created.append('operator')
    db.session.commit()
    if created:
        return f"Created users: {', '.join(created)}"
    return "Users already exist"

# Временный маршрут для исправления ENUM userrole
@app.route('/fix_enum')
def fix_enum():
    try:
        # Удаляем старый ENUM если он существует
        db.session.execute(text("DROP TYPE IF EXISTS userrole CASCADE;"))
        # Создаем новый ENUM с правильными значениями
        db.session.execute(text("CREATE TYPE userrole AS ENUM ('ADMIN', 'OPERATOR');"))
        db.session.commit()
        return "ENUM userrole successfully recreated with ADMIN and OPERATOR values"
    except Exception as e:
        db.session.rollback()
        return f"Error fixing ENUM: {str(e)}"

# Временный маршрут для применения миграций
@app.route('/apply_migrations')
def apply_migrations():
    try:
        from app import db
        from app.models import User, RawMaterialType, RawMaterial, Product, RecipeTemplate, RecipeItem, ProductionPlan, ProductionBatch, BatchMaterial, MaterialBatch
        
        # Сначала создаем ENUM userrole
        db.session.execute(text("DROP TYPE IF EXISTS userrole CASCADE;"))
        db.session.execute(text("CREATE TYPE userrole AS ENUM ('admin', 'operator');"))
        db.session.commit()
        
        # Удаляем все таблицы
        db.drop_all()
        
        # Создаем все таблицы заново
        db.create_all()
        
        return "ENUM created and all tables recreated successfully"
    except Exception as e:
        db.session.rollback()
        return f"Error creating tables: {str(e)}" 