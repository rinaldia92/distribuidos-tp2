# Trabajo práctico N° 2: COVID19 Statistics
## Sistemas Distribuidos I (75.74)

<h1 align="center">
  <img src="./images/logofiuba.jpg" alt="logo fiuba">
</h1>

## Autor: Alan Rinaldi
## Fecha: 11 de junio 2020




## Indice:

   - [1- Objetivo](#1--objetivo)
   - [2- Vista Logica](#2--vista-logica)
   - [3- Vista de Desarrollo](#3--vista-de-desarrollo)
   - [4- Vista de Proceso](#2--vista-de-proceso)
   - [5- Vista Fisica](#2--vista-fisica)
   - [6- Casos de uso](#3--casos-de-uso)
   - [7- Cosas a mejorar](#4--cosas-a-mejorar)


## 1- Objetivo

Se solicita un sistema distribuido que procese estadísticas de datos individuales sobre casos positivos y decesos con info geo-espacial.
Retornando:
* Totales de nuevos casos positivos y decesos por día.
* Listado de las 3 regiones con más casos positivos.
* Porcentaje de decesos respecto de cantidad de casos positivos detectados.

&nbsp;

## 2- Vista Logica

Se modeló al sistema como un **pipeline**, en el cual en cada etapa se procesa la informacion recibida de la etapa anterior y se la envia a la etapa siguiente.
Se realizó el siguiente **DAG** para mostrar como es el sistema.

<img src="/images/dag.svg">

Detalle de los nodos del **DAG**:
* Init: Encargado de leer los casos y de insertarlos al sistema.
* FIlter Parser: Encagado de parsear la información recibida y enviar la información con su respectivo formato a los siguientes nodos.
* Counter: Encargado de recibir los casos (positivos y decesos), acumularlos y enviarlos al siguiente nodo.
* Percentage: Encargado de recibir la cantidad de positivos y decesos parciales de cada **Counter**, al finalizar calcula el porcentaje y lo envia al nodo final.
* Counter By Date: Encargado de recibir los casos (positivos y decesos) junto a la fecha, acumularlos por fecha y enviarlos al siguiente nodo.
* Total By Date: Encargado de recibir las cantidades de positivos y decesos por fecha parciales de cada **Counter By Date** y enviar el total al nodo final.
* Init Regions: Encargado de leer las regiones y su locacion y enviarlas al nodo **Distance**.
* Distance: Luego de recibir las regiones de **Init Regions** recibe las locaciones de los casos positivos de **Filter**, calcula la region mas cercana y la envia al siguiente nodo.
* Counter By Region: Encargado de recibir las regiones con caso positivos de **Distance**, las acumula y envia al siguiente nodo.
* Total By Region: Encargado de recibir la cantidad de positivos por region parciales de **Distance**, las acumula y calcula las 3 regiones con mas casos positivos y las envia al nodo final.
* End: Encagargado de recibir los resultados totales.

## 3- Vista de Desarrollo

Este sistema posee 12 módulos, de los cuales 11 son de para cada uno de los nodos y uno de **middleware** para realizar la comunicación entre cada uno de estos módulos.

<img src="/images/desarrollo.svg">

## 4- Vista de Proceso

Los nodos **Init**, **Init Regions** son procesos de multiplicidad unica, ya que son los encargados de leer los casos y regiones para inyectarlos al sistema.
Los nodos **Percentage**, **Total By Date**, **Total By Region** y **End** son procesos de multiplicidad unica ya que son los encargados de acumular los valores totales.
Los nodos **Distance**, **Counter**, **Counter By Date** y **Counter By Region** son procesos escalables.

<img src="/images/proceso.svg">

En el siguiente diagrama de actividades se puede observar la coordinación entre el proceso **Distance** y el proceso **Counter By Region**.

<img src="/images/actividades.svg">

## 5- Vista Fisica

Todos los procesos del pipeline se ejecutan en su propio container de docker, para comunicarse entre si se utilizan las colas de **RabbitMQ** cuyo servidor se encuentra en otro container.

<img src="/images/despliegue.svg">

## 6- Casos de uso

Como fue explicado en los objetivos hay 3 casos de uso:
* Totales de nuevos casos positivos y decesos por día.
* Listado de las 3 regiones con más casos positivos.
* Porcentaje de decesos respecto de cantidad de casos positivos detectados.

## 7- Cosas a mejorar

Las principales cosas a mejorar son:
* Mejorar el middleware para no necesitar saber la cantidad de workers.
* Mejorar la forma de informar que se deja de procesar.