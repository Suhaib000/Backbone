from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouterViewSet , RollbackDetialViewSet

router = DefaultRouter()
router.register(r'routers', RouterViewSet)
router.register(r'rollback', RollbackDetialViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
