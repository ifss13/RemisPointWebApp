from django.http import JsonResponse
from firebase_admin import messaging # Asegúrate de importar la configuración de Firebase

def enviar_notificacion(request):
    # El token del usuario al que quieres enviar la notificación
    token = 'fVMWEvT3luK4S5hCaDCn9q:APA91bH4n5mif1UrMlvab9yciPhIu_mx3CWWI0kZiZ3FFzCmXM_YTVoTOHorwYnkimgZ5nKYJr5fqbdkqp5jFvof9oARD2-vZR_9l1TLD1Xe_3NDcCRlSDc'

    # Mensaje de la notificación
    message = messaging.Message(
        notification=messaging.Notification(
            title='Título de la Notificación',
            body='Cuerpo de la Notificación',
        ),
        token=token,
    )

    # Enviar la notificación
    response = messaging.send(message)
    return JsonResponse({'success': True, 'message_id': response})
