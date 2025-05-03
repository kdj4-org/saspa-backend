from rest_framework.test import APITestCase
from rest_framework import status
from app.models import Servicio

class ServicioAdminTests(APITestCase):

    def setUp(self):
        self.base_url = '/admin/servicios/'

        self.servicio_data = {
            "nombre": "Manicure",
            "descripcion": "Corte personalizado",
            "duracion_minutos": 45,
            "precio": 10000
        }

    def test_crear_servicio(self):
        response = self.client.post(self.base_url, self.servicio_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mensaje'], "Servicio creado correctamente.")
        self.assertTrue(Servicio.objects.filter(nombre="Manicure").exists())


    def test_modificar_servicio(self):
        servicio = Servicio.objects.create(**self.servicio_data)
        url = f"{self.base_url}{servicio.id}/"
        updated_data = {
            "nombre": "Manicure Deluxe",
            "descripcion": "Corte y esmalte",
            "duracion_minutos": 60,
            "precio": 15000
        }
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mensaje'], "Servicio actualizado correctamente.")
        servicio.refresh_from_db()
        self.assertEqual(servicio.nombre, "Manicure Deluxe")

    def test_eliminar_servicio(self):
        servicio = Servicio.objects.create(**self.servicio_data)
        url = f"{self.base_url}{servicio.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mensaje'], "Servicio eliminado correctamente.")
        self.assertFalse(Servicio.objects.filter(id=servicio.id).exists())

