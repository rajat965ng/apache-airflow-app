```
    _                     _               _    _       __ _               
   / \   _ __   __ _  ___| |__   ___     / \  (_)_ __ / _| | _____      __
  / _ \ | '_ \ / _` |/ __| '_ \ / _ \   / _ \ | | '__| |_| |/ _ \ \ /\ / /
 / ___ \| |_) | (_| | (__| | | |  __/  / ___ \| | |  |  _| | (_) \ V  V / 
/_/   \_\ .__/ \__,_|\___|_| |_|\___| /_/   \_\_|_|  |_| |_|\___/ \_/\_/  
        |_|                                                               
```

## What is Apache Airflow ?
- A platform for programmatically developing and monitoring batch data pipelines.
- Provides a Python framework to develop data pipelines composed of different technologies.
- Airflow pipelines themselves are also defined in Python scripts.

### Introducing workflow managers
- Many computational processes are composed of multiple actions that are required to be executed in a 
  sequence and at a regular interval.
- The process are expressed as graph of tasks
  - which individual actions make up the process.
  - which order these actions need to be executed.
- These graphs are often called **workflows**.

### Workflow as a series of tasks
- **workflows**, which define a collection of tasks to be run, as well as the dependencies between these tasks (i.e., which tasks need to be run first).
- **Core Concept**: defining tasks as 'units of work' and expressing dependencies between these tasks.
  - This allows workflow management systems to track which tasks should be run when, while also taking care of features such as parallelism, automatic retries of failing jobs, and reporting.

#### Expressing task dependencies

- **task dependencies**: 
  - Relationships between tasks determine when to run a given task. 
  - Which tasks are upstream of the given task (pointing to the task dependencies) or saying which tasks are downstream of the task (marking the task as a dependency of other tasks).

#### Task execution model of workflow management systems
- Workflow management systems is either via a push or pull model.
  - **push model**, a central process pushes work to execute to a worker process.
  - **pull (or poll) model** works by workers continuously polling a central scheduler process checking if there’s new work to pick up.
- In Airflow, there is a central process called the **“scheduler”** which pushes tasks to execute to **workers**.

### An overview of the Airflow architecture

![](.README/49c8160f.png)

- Airflow consists of:
  - webserver: 
    - provides the visual interface to the user to view and manage the status of workflows.
  - scheduler: 
    - parsing DAG definitions.
    - determining which tasks should be started (scheduled/manually triggered/backfilled).
    - sending tasks to the workers to execute.
  - Worker
  
### Directed Acyclic Graphs
- Cycles would create unsatisfiable dependencies in workflows (we would never know when a pipeline is finished).
- Because of this acyclic property, workflows are modelled as Directed Acyclic Graphs (DAG).
- In Airflow you create and schedule pipelines of tasks by creating a DAG.

### Batch processing
- Airflow operates in the space of batch processes; a series of finite tasks with clearly defined start and end tasks, to run at certain intervals or triggers.
- When used in combination with Airflow, this is always a Spark batch job and not a Spark streaming job because the batch job is finite and a streaming job could run forever.  

### Scheduling and backfilling
- When you want to run a new logic on all previously completed workflows, on all historical data.
- This is possible in Airflow with a mechanism called **backfilling**, running workflows back in time.
- If the fetching of data is not possible back in time, or is a very lengthy process you’d like to avoid, you can rerun partial workflows with backfilling.

### Handling Failures
- Airflow provides various ways for handling failures, varying from for example stating, “It’s okay—continue running other tasks”, to “retry this one failed task for a maximum of 5 times” to “failure here is unacceptable — fail the entire pipeline.”


## Anatomy of an Airflow DAG

### Collecting data from numerous sources

#### Exploring the data
- ```curl -X GET "https://ll.thespacedevs.com/2.0.0/launch/" | jq -rc ```

![](.README/b1cc0792.png)

#### Writing your first Airflow DAG
- We can split a large job, which consists of one or more steps, into individual “tasks” and together form a Directed Acyclic Graph (DAG). Multiple tasks can be run in parallel, and tasks can run different technologies.
- For example, we could first run a Bash script and next run a Python script.
- Fetching the data for the next five rocket launches was a single curl command in Bash, which is easily executed with the BashOperator. However, parsing the JSON result, selecting the image URLs from it and downloading the respective images requires a bit more effort.
- The PythonOperator in Airflow is responsible for running any Python code.

- ```docker run -p 8080:8080 -v $PWD/dags:/root/airflow/dags  airflowbook/airflow```

- ![](.README/622f96bd.png)

- ![](.README/ae94ea0e.png)

- ![](.README/9f52158a.png)

#### Tasks vs operators

|Tasks|Operators|
|-----|---------|
|Tasks in Airflow manage the execution of an Operator.|they exist to perform one single piece of work.|
|The user can focus on the work to be done by using operators, while Airflow ensures correct execution of the work via tasks.|Some operators perform generic work such as the BashOperator (used to run a Bash script) and the PythonOperator (used to run a Python function). Others have more specific use cases such as the EmailOperator (used to send an email) or the HTTPOperator (used to call an HTTP endpoint).|
|They can be thought of as a small “wrapper” or “manager” around an operator that ensures the operator executes correctly.|Airflow has a class called BaseOperator and many subclasses inheriting from the BaseOperator such as the PythonOperator, EmailOperator, and OracleOperator.|

#### Running at regular intervals
- In Airflow, we can schedule a DAG to run at certain intervals -- once an hour, day or month. This is controlled on the DAG by setting the **schedule_interval** argument:

#### Handling failing tasks
- **Successfully completed tasks**: Only green in the Airflow UI.
- **Specific failed task**: Would be displayed in red in both the graph and tree views.
- **Dependent failed task**: Such task instances are displayed in orange.

- It would be unnecessary to restart the entire workflow. A nice feature of Airflow is that you can restart from the point of failure and onwards, without having to restart any previously succeeded tasks.

## Scheduling in Airflow

- We will dive a bit deeper into the concept of scheduling in Airflow and explore how this allows you to process data incrementally at regular intervals.
  - we’ll introduce a small use case focussed on analyzing user events from our website and explore how we can build a DAG to analyze these events at regular intervals. 
  - Next, we’ll explore ways to make this process more efficient by taking an incremental approach to analyzing our data and how this ties into Airflow’s concept of execution dates.
  - Finally, we’ll finish by showing how we can fill in past gaps in our dataset using backfilling and discussing some important properties of proper Airflow tasks.