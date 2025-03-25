from django.urls import path
from . import views_admin

urlpatterns = [
    path('form-cliente/', views_admin.cargar_form_cliente, name='nuevo_cliente'),
    path('form-cliente/<int:cliente_id>/', views_admin.cargar_form_cliente, name='editar_cliente'),
    path('guardar-cliente/', views_admin.guardar_cliente, name='guardar_cliente'),
    path('guardar-cliente/<int:cliente_id>/', views_admin.guardar_cliente, name='guardar_cliente_editar'),
    path('eliminar-cliente/<int:cliente_id>/', views_admin.eliminar_cliente, name='eliminar_cliente'),
    path('form-chofer/', views_admin.cargar_form_chofer, name='nuevo_chofer'),
    path('form-chofer/<int:chofer_id>/', views_admin.cargar_form_chofer, name='editar_chofer'),
    path('guardar-chofer/', views_admin.guardar_chofer, name='guardar_chofer'),
    path('guardar-chofer/<int:chofer_id>/', views_admin.guardar_chofer, name='guardar_chofer_editar'),
    path('eliminar-chofer/<int:chofer_id>/', views_admin.eliminar_chofer, name='eliminar_chofer'),
    path('form-viaje/', views_admin.cargar_form_viaje, name='nuevo_viaje'),
    path('form-viaje/<int:viaje_id>/', views_admin.cargar_form_viaje, name='editar_viaje'),
    path('guardar-viaje/', views_admin.guardar_viaje, name='guardar_viaje'),
    path('guardar-viaje/<int:viaje_id>/', views_admin.guardar_viaje, name='guardar_viaje_editar'),
    path('eliminar-viaje/<int:viaje_id>/', views_admin.eliminar_viaje, name='eliminar_viaje'),
    path('form-remiseria/', views_admin.cargar_form_remiseria, name='nueva_remiseria'),
    path('form-remiseria/<int:remiseria_id>/', views_admin.cargar_form_remiseria, name='editar_remiseria'),
    path('guardar-remiseria/', views_admin.guardar_remiseria, name='guardar_remiseria'),
    path('guardar-remiseria/<int:remiseria_id>/', views_admin.guardar_remiseria, name='guardar_remiseria_editar'),
    path('eliminar-remiseria/<int:remiseria_id>/', views_admin.eliminar_remiseria, name='eliminar_remiseria'),
    path('form-localidad/', views_admin.cargar_form_localidad, name='nueva_localidad'),
    path('form-localidad/<int:localidad_id>/', views_admin.cargar_form_localidad, name='editar_localidad'),
    path('guardar-localidad/', views_admin.guardar_localidad, name='guardar_localidad'),
    path('guardar-localidad/<int:localidad_id>/', views_admin.guardar_localidad, name='guardar_localidad_editar'),
    path('eliminar-localidad/<int:localidad_id>/', views_admin.eliminar_localidad, name='eliminar_localidad'),

]
