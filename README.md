# Computador Descentralizado con Docker y Flask

Este proyecto simula un computador descentralizado utilizando contenedores Docker conectados mediante la interfaz de red `bat0`, basada en BATMAN Advanced. Cada contenedor actúa como un nodo que participa en la validación de transacciones, y la comunicación entre ellos se representa visualmente en una interfaz web desarrollada con Flask.

## Objetivo

El propósito de este proyecto es demostrar de forma práctica cómo puede construirse un sistema descentralizado que mantenga la sincronización, robustez y comunicación entre nodos. Está diseñado con fines educativos para explicar cómo funciona una red distribuida utilizando herramientas modernas y accesibles.

## Características

- Simulación de nodos conectados en red mesh utilizando `batctl` y la interfaz `bat0`.
- Interfaz web creada con Flask para visualizar la red de nodos y las transacciones.
- Validación distribuida de transacciones entre contenedores.
- Comunicación entre nodos mediante HTTP y Redis como sistema de mensajes.
- Contenedores configurados para funcionar como una malla descentralizada.

## Tecnologías utilizadas

- Docker
- Python
- Flask
- Redis
- requests (librería de Python)
- batctl (BATMAN Advanced)

## Requisitos

- Docker instalado y funcionando
- Sistema operativo compatible con BATMAN Advanced (Linux)
- Permisos administrativos para crear y manipular interfaces de red

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/so-fivs/docker.git
cd docker
