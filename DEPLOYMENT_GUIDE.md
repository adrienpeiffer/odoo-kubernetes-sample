# 🚀 Guía de Despliegue de Odoo en Kubernetes (Digital Ocean)

## 📋 **Prerrequisitos**

### **Herramientas Necesarias**
- `kubectl` configurado para tu cluster de Digital Ocean
- `helm` instalado
- Acceso al cluster de Kubernetes

### **Cluster de Kubernetes**
- Cluster de Digital Ocean funcionando
- Namespace `default` disponible
- Storage persistente habilitado

## 🔧 **Paso 1: Instalar CloudNativePG Operator**

### **Problema Identificado**
Los manifests directos de CloudNativePG fallan con errores de anotaciones largas:
```
The CustomResourceDefinition "poolers.postgresql.cnpg.io" is invalid: 
metadata.annotations: Too long: may not be more than 262144 bytes
```

### **Solución: Usar Helm**
```bash
# Agregar repositorio de CloudNativePG
helm repo add cnpg https://cloudnative-pg.github.io/charts

# Actualizar repositorios
helm repo update

# Instalar CloudNativePG operator
helm install cnpg cnpg/cloudnative-pg --namespace cnpg-system --create-namespace
```

### **Verificar Instalación**
```bash
# Verificar pods del operador
kubectl get pods -n cnpg-system

# Verificar CRDs instalados
kubectl get crd | grep postgresql
```

## 🔧 **Paso 2: Instalar Nginx Ingress Controller**

### **Problema Identificado**
El Ingress de Odoo no funciona sin un controlador de Ingress:
```
Address: (sin dirección IP)
Ingress Class: <none>
```

### **Solución: Instalar Nginx Ingress Controller**
```bash
# Instalar Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Verificar instalación
kubectl get pods -n ingress-nginx
```

### **Verificar Funcionamiento**
```bash
# Verificar service del controlador
kubectl get service -n ingress-nginx

# Verificar que tenga IP externa
kubectl get service -n ingress-nginx ingress-nginx-controller
```

## 🔧 **Paso 3: Configurar Ingress para Digital Ocean**

### **Problema Identificado**
El Ingress original usa `host: localhost`, que no funciona en clusters remotos.

### **Solución: Host Vacío**
```yaml
spec:
  rules:
    - host: ""  # Empty host for any domain/IP access
      http:
        paths:
          - path: /
            backend:
              service:
                name: odoo
                port:
                  number: 8069
```

### **Configuración Final del Ingress**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odoo
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
    - host: ""  # Empty host for any domain/IP access
      http:
        paths:
          - backend:
              service:
                name: odoo
                port:
                  number: 8069
            path: /
            pathType: Prefix
```

## 🔧 **Paso 4: Problemas con Imágenes de Odoo**

### **Problema 1: Imagen Personalizada con Errores**
La imagen `yusuke1998/kubernetes-odoo:16` tiene errores de compatibilidad:
```
TypeError: get_response() takes from 1 to 2 positional arguments but 3 were given
```

### **Problema 2: Imagen OCA sin Scripts**
La imagen `ghcr.io/oca/oca-ci/py3.10-odoo16.0:latest` no tiene el script `/entrypoint-dbbase`:
```
exec: "/entrypoint-dbbase": stat /entrypoint-dbbase: no such file or directory
```

### **Solución: Imagen Oficial de Odoo**
```yaml
containers:
  - name: odoo
    image: odoo:16.0
    imagePullPolicy: Always
```

## 🔧 **Paso 5: Problemas con Init Container**

### **Problema Identificado**
El init container personalizado falla porque:
1. **Script no existe** en las imágenes
2. **Inicialización manual** no es necesaria
3. **Complejidad innecesaria** para despliegue básico

### **Solución: Eliminar Init Container**
```yaml
# Comentar o eliminar initContainers
# initContainers:
#   - name: odoo-init
#     image: odoo:16.0
#     args:
#       - /entrypoint-dbbase
```

## 🔧 **Paso 6: Configuración de PostgreSQL**

### **Configuración del Cluster**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres
spec:
  imageName: ghcr.io/cloudnative-pg/postgresql:16.3
  imagePullPolicy: Always  # Importante para Digital Ocean
  instances: 1
  storage:
    size: 10Gi
```

### **Variables de Entorno Necesarias**
```yaml
env:
  - name: PGUSER
    valueFrom:
      secretKeyRef:
        key: username
        name: postgres-app
  - name: PGPASSWORD
    valueFrom:
      secretKeyRef:
        key: password
        name: postgres-app
```

## 🔧 **Paso 7: Despliegue Final**

### **Comando de Aplicación**
```bash
# Aplicar todos los manifests
kubectl apply -k manifests/

# O aplicar individualmente
kubectl apply -f manifests/postgresql.yaml
kubectl apply -f manifests/odoo-deployment.yaml
kubectl apply -f manifests/odoo-service.yaml
kubectl apply -f manifests/odoo-ingress.yaml
```

### **Verificación del Despliegue**
```bash
# Verificar pods
kubectl get pods

# Verificar services
kubectl get services

# Verificar ingress
kubectl get ingress

# Verificar cluster PostgreSQL
kubectl get cluster postgres
```

## 🌐 **Acceso a la Aplicación**

### **URL de Acceso**
```
http://[IP-DEL-INGRESS-CONTROLLER]
```

### **Ejemplo**
```
http://157.230.202.66
```

## ⚠️ **Problemas Comunes y Soluciones**

### **1. Pod Affinity Rules**
```yaml
# Comentar temporalmente para permitir despliegue
# affinity:
#   podAffinity:
#     requiredDuringSchedulingIgnoredDuringExecution:
#       - labelSelector:
#           matchExpressions:
#             - key: cnpg.io/cluster
#               operator: Exists
```

### **2. ImagePullPolicy**
```yaml
# Para Digital Ocean, usar Always o IfNotPresent
imagePullPolicy: Always  # NO usar Never
```

### **3. Addons OCA**
Los addons OCA no están disponibles en PyPI:
```txt
# requirements.in
# odoo-addon-fs_attachment  # NO disponible en PyPI
# odoo-addon-session_db     # NO disponible en PyPI
```

## 🎯 **Resumen de Dependencias Críticas**

1. ✅ **CloudNativePG Operator** (via Helm)
2. ✅ **Nginx Ingress Controller** (via kubectl)
3. ✅ **Imagen oficial de Odoo** (`odoo:16.0`)
4. ✅ **Configuración de Ingress** para Digital Ocean
5. ✅ **Eliminación de init containers** problemáticos

## 📚 **Recursos Adicionales**

- [CloudNativePG Documentation](https://cloudnative-pg.io/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Odoo Docker Hub](https://hub.docker.com/_/odoo)
- [OCA Addons](https://github.com/OCA)

## 🏆 **Estado Final**

Con esta configuración, Odoo debería estar:
- ✅ **Funcionando** correctamente en Kubernetes
- ✅ **Accesible** desde Internet via Ingress
- ✅ **Conectado** a PostgreSQL funcional
- ✅ **Listo** para uso en producción
