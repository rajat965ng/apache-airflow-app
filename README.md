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

```
from datetime import datetime
import pandas as pd
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

dag = DAG(
   dag_id="user_events",
   start_date=datetime(2015, 6, 1),
   schedule_interval=None,
)

fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command="curl -o data/events.json https://localhost:5000/events",
    dag=dag, 
)


def _calculate_stats(input_path, output_path):
    """Calculates event statistics."""
    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index()  
    stats.to_csv(output_path, index=False)

calculate_stats = PythonOperator(
   task_id="calculate_stats",
   python_callable=_calculate_stats,
   op_kwargs={
       "input_path": "data/events.json",
       "output_path": "data/stats.csv",
   },
   dag=dag, 
)
```

### Running at regular intervals
- Schedule intervals can be defined using the schedule_interval argument when initializing the DAG.
- By default, the value of this argument is None, which means that the DAG will not be scheduled and will only be run when triggered manually from the UI or the API.

#### Defining scheduling intervals
- Airflow provides the convenient macro “@daily” for defining a daily scheduled interval which runs our DAG once every day at midnight:

- For example, say we define our DAG with a start date on the first of January:
```
import datetime as dt
dag = DAG(
    dag_id="user_events",
    schedule_interval="@daily", 
    start_date=dt.datetime(year=2019, month=1, day=1)
)
```

- Without an end date, Airflow will (in principle) keep executing our DAG on this daily schedule until the end of time. However, if we already know that our project has a fixed duration, we can tell Airflow to stop running our DAG after a certain date using the `end_date` parameter:
```
dag = DAG(
    dag_id="user_events",
    schedule_interval="@daily", 
    start_date=dt.datetime(year=2019, month=1, day=1), 
    end_date=dt.datetime(year=2019, month=1, day=5),
)
```

#### Cron-based intervals
- To support more complicated scheduling intervals, Airflow allows us to define scheduling intervals using the same syntax as used by cron, a time-based job scheduler used by Unix-like computer operating systems such as macOS and Linux.

```
# ┌─────── minute (0 - 59)
# │ ┌────── hour (0 - 23)
# │ │ ┌───── day of the month (1 - 31)
# │ │ │ ┌───── month (1 - 12)
# │ │ │ │ ┌──── day of the week (0 - 6) (Sunday to Saturday; # │ │ │ │ │ 7 is also Sunday on some systems) 
# * * * * *
```

-  For example, we can define hourly, daily and weekly intervals using the following cron expressions:
```
• 0 * * * * = hourly (running on the hour)
• 0 0 * * * = daily (running at midnight)
• 0 0 * * 0 = weekly (running at midnight on Sunday)
```

-  We can also define more complicated expressions such as the following:
```
• 0 0 1 * * = midnight on the first of every month
• 45 23 * * SAT = 23:45 every Saturday
```

- we can build expressions that enable running jobs on multiple weekdays or multiple sets of hours during a day:
```
• 0 0 * * MON,WED,FRI = run every Monday, Wednesday, Friday at midnight
• 0 0 * * MON-FRI = run every weekday at midnight
• 0 0,12 * * * = run every day at 00:00AM and 12:00P.M.
```

- Airflow also provides support for several macros that represent shorthands for commonly used scheduling intervals.

|Preset|Meaning|
|------|-------|
|@once|Schedule once and only once|
|@hourly|Run once an hour at the beginning of the hour|
|@daily|Run once a day at midnight|
|@weekly|Run once a week at midnight on Sunday morning|
|@monthly|Run once a month at midnight on the first day of the month|
|@yearly|Run once a year at midnight on January 1|

#### Frequency-based intervals
- You could write an expression that runs on every 1st, 4th, 7th, etc. day of the month, but this approach would run into problems at the end of the month as the DAG would run consecutively on both the 31st and the 1st of the next month, violating the desired schedule.
- what if we really want to run our DAG on a three-daily schedule?
- Airflow also allows you to define scheduling intervals in terms of a relative time interval.
- To use such a frequency-based schedule, you can pass a “timedelta” instance (from the datetime module in the standard library) as a schedule interval:

```
from datetime import timedelta 

dag = DAG(
    dag_id="user_events", 
    schedule_interval=timedelta(days=3), 
    start_date=dt.datetime(year=2019, month=1, day=1),
)
```

### Processing data incrementally

#### Fetching events incrementally
- assuming we stuck with the @daily schedule
- For one, our DAG is downloading and calculating statistics for the entire catalogue of user events every day, which is hardly efficient.
- Moreover, this process is only downloading events for the past 30 days, which means that we are not building up any history for dates further in the past.
- One way to solve these issues is to change our DAG to load data in an incremental fashion, in which we only load events from the corresponding day in each schedule interval and only calculate statistics for the new events.

![](.README/90df4456.png)

- We can implement this incremental data fetching in our DAG by changing our bash command to include the two dates:

````
fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command="curl -o data/events.json http://localhost:5000/events?start_date=2019-01-01&end_date=2019-01-02", 
    dag=dag,
)
````

#### Dynamic time references using execution dates
- **execution_date**: 
  - which represents the date and time for which our DAG is being executed.
  - the ```execution_date``` is not a date but a timestamp, which reflects the start time of the schedule interval for which the DAG is being executed.
- **next_execution_date**:
  - The end time of the schedule interval is indicated by another parameter.
- **previous_execution_date**:
  - describes the start of the previous schedule interval.
  - it can be useful for performing analyses that contrast data from the current time interval with results from the previous interval.
  
```
fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=("curl -o data/events.json " "http://localhost:5000/events?" "start_date={{execution_date.strftime('%Y-%m-%d')}}&end_date={{next_execution_date.strftime('%Y-%m-%d')}}" ),
    dag=dag,
)
```

- Airflow also provides several short hand parameters for common date formats.
  - **ds** and **ds_nodash** parameters are different representations of the execution_date, formatted as YYYY-MM-DD and YYYYMMDD respectively.
  - **next_ds**, **next_ds_nodash**, **prev_ds** and **prev_ds_nodash** provide shorthands for the next and previous execution dates, respectively.
  
```
fetch_events = BashOperator(
   task_id="fetch_events",
   bash_command="curl -o data/events.json http://localhost:5000/events?start_date={{ds}}&end_date={{next_ds}}", 
   dag=dag,
)
```

#### Partitioning your data
- To avoid new task is simply overwriting the result of the previous day, meaning that we are effectively not building up any history.
- One way to solve this problem is to simply append new events to the events.json file, which would allow us to build up our history in a single JSON file.
  -  a drawback of this approach is that it requires any downstream processing jobs to load the entire dataset, even if we are only interested in calculating statistics for a given day.
  -  it also makes this file a single point of failure, by which we may risk losing our entire dataset should this file become lost or corrupted.

```
fetch_events = BashOperator( 
    task_id="fetch_events",
    bash_command="curl -o data/events/{{ds}}.json http://localhost:5000/events?start_date={{ds}}&end_date={{next_ds}}",
    dag=dag,
)
```

- This practice of dividing a dataset into smaller, more manageable pieces is a common strategy in data storage and processing systems. 
- The practice is commonly referred to as partitioning, with the smaller pieces of a dataset being referred to as partitions.
- The advantage of partitioning our dataset by execution date becomes evident when we consider the second task in our DAG (calculate_stats), in which we calculate statistics for each day’s worth of user events.

```
def _calculate_stats(input_path, output_path):
    """Calculates event statistics."""
    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index() 
    stats.to_csv(output_path, index=False)

calculate_stats = PythonOperator( 
    task_id="calculate_stats", 
    python_callable=_calculate_stats, 
    op_kwargs={
        "input_path": "data/events.json",
        "output_path": "data/stats.csv", 
    },
    dag=dag, 
)
```

```
def _calculate_stats(**context):
    """Calculates event statistics."""
    input_path = context["templates_dict"]["input_path"] 
    output_path = context["templates_dict"]["output_path"]
    events = pd.read_json(input_path)
    stats = events.groupby(["date", "user"]).size().reset_index()
    stats.to_csv(output_path, index=False)
    
    
calculate_stats = PythonOperator(
   task_id="calculate_stats",
   python_callable=_calculate_stats,
   templates_dict={
       "input_path": "data/events/{{ds}}.json",
       "output_path": "data/stats/{{ds}}.csv",
   },
   provide_context=True, 
   dag=dag,
)
```

#### Using backfilling to fill in past gaps
- By default, Airflow will schedule and run any past schedule intervals that have not yet been run.
- Specifying a past start date and activating the corresponding DAG will result in all intervals that have passed before the current time being executed.
- This behaviour is controlled by the DAG catchup parameter and can be disabled by setting **catchup** to False:

```
dag = DAG(
    dag_id="user_events", 
    schedule_interval=timedelta(days=3), 
    start_date=dt.datetime(year=2019, month=1, day=1), 
    catchup=False,
)
```

- Although backfilling is a powerful concept, it is limited by the availability of data in source systems. 

### Best Practices for Designing Tasks

#### Atomicity
- A Sending an email after writing to CSV creates two pieces of work in a single function, which breaks atomicity of the task.
- To implement this functionality in an atomic fashion, we could simply split the email functionality out into a separate task:

```
def _send_stats(email, **context):
    stats = pd.read_csv(context["templates_dict"]["stats_path"]) 
    email_stats(stats, email=email)
    
send_stats = PythonOperator(
    task_id="send_stats",
    python_callable=_send_stats,
    op_kwargs={"email": "user@example.com"},
    templates_dict={"stats_path": "data/stats/{{ds}}.csv"},
    provide_context=True,
    dag=dag, 
)
```

#### Idempotency
- Tasks are said to be idempotent if calling the same task multiple times with the same inputs has no additional effect.

```
fetch_events = BashOperator( 
    task_id="fetch_events",
    bash_command="curl -o data/events/{{ds}}.json http://localhost:5000/events?start_date={{ds}}&end_date={{next_ds}}",
    dag=dag,
)
```

- Re-running this task for a given date would result in the task fetching the same set of events as its previous execution.
- overwrite the existing JSON file in the data/events folder, producing the same end result.

- an example of a non-idempotent task, consider the situation in which we discussed using a single JSON file (data/events.json) and simply appending events to this file.

## Templating Tasks Using the Airflow Context

### Inspecting data for processing with Airflow
-  For the purposes of this example, we will apply the axiom that an increase in a company’s pageviews shows a positive sentiment, and the company’s stock is likely to increase as well.
-  On the other hand, a decrease in page views tells us a loss in interest, and the stock price is likely to decrease.

#### Determining how to load incremental data
- In order to develop a data pipeline, we must understand how to load it in an incremental fashion and how to work the data:

- Data Source: ```https://dumps.wikimedia.org/other/pageviews/2019/2019-07/pageviews-20190701-010000.gz```

#### Task context & Jinja templating
- The url is constructed of various date & time components:  ```https://dumps.wikimedia.org/other/pageviews/{year}/{year}-{month}/pageviews-{year}{month}{day}-{hour}0000.gz```

- Bash Operator
  - Bash Command:
    ```curl -o /tmp/wikipageviews.gz https://dumps.wikimedia.org/other/pageviews/{{ execution_date.year }}/{{ execution_date.year }}-{{ '{:02}'.format(execution_date.month) }}/pageviews-{{ execution_date.year }}{{ '{:02}'.format(execution_date.month) }}{{ '{:02}'.format(execution_date.day) }}-{{ '{:02}'.format(execution_date.hour) }}0000.gz```
  
  - The double curly braces denote a Jinja templated string. Jinja is a templating engine, which replaces variables and/or expressions in a templated string at runtime.  
    ```{{ '{:02}'.format(execution_date.hour) }}```
 
- Python Operator
  - The PythonOperator is an exception to this standard, because it doesn’t take arguments which can be templated with the runtime context, but instead a **python_callable** argument in which the runtime context can be applied.
    - Way 1: retrieve args in method parameters
    ```
        def _get_data(execution_date, **_):
         year, month, day, hour, *_ = execution_date.timetuple()
         url = (
             "https://dumps.wikimedia.org/other/pageviews/"
            f"{year}/{year}-{month:02}/pageviews-{year}{month:02}{day:02}-{hour:02}0000.gz" )
        
         output_path = "/tmp/wikipageviews.gz" 
         request.urlretrieve(url, output_path)
    ```
  - A Keyword arguments can be captured with two asterisks (**). A convention is to name the “capturing” argument kwargs.  
  - Print start and end date of interval
    - Way 2: Retrieve args in method body
    ```
        def _print_context(**context):
         start = context["execution_date"] 
         end = context["next_execution_date"]
         print(f"Start: {start}, end: {end}")
    ```
    
  - Providing user-defined variables to the PythonOperator callable
      ```
      get_data = PythonOperator( 
        task_id="get_data", 
        python_callable=_get_data, 
        provide_context=True, 
        op_args=["/tmp/wikipageviews.gz"], #or op_kwargs={"output_path": "/tmp/wikipageviews.gz"},
        dag=dag,
      )
      ```
   - **output_path** in can be the first argument in the **_get_data** function, the value of it will be set to **“/tmp/wikipageviews.gz”**.
    

### Hooking up other systems
- two operators will extract the archive and process the extracted file by scanning over it and selecting the pageview counts for the given page names.

- CREATE TABLE statement for storing output
  
  ```
  CREATE TABLE pageview_counts (
      pagename VARCHAR(50) NOT NULL,
      pageviewcount INT NOT NULL,
      datetime TIMESTAMP NOT NULL
  );
  ```    
  
- Postgres is an external system and Airflow supports connecting to a wide range of external systems with the help of many operators in the Airflow ecosystem.
  - ```pip3.9 install apache-airflow[postgres]```

  - ```
        airflow connections --add 
        --conn_id my_postgres   <- connection identifier
        --conn_type postgres
        --conn_host localhost
        --conn_login postgres
        --conn_password mysecretpassword
    ```
## Complex task dependencies

### Basic dependencies
#### Linear dependencies
```
download_launches = BashOperator(...)
get_pictures = PythonOperator(...)
notify = BashOperator(...)
```  
#### Fan in/out dependencies
```
# Fan out (one-to-multiple).
start >> [fetch_weather, fetch_sales]
# Note that this is equivalent to:
# start >> fetch_weather
# start >> fetch_sales
```
```
# Fan in (multiple-to-one), defined in one go.
[preprocess_weather, preprocess_sales] >> build_dataset
# This notation is equivalent to defining the
# two dependencies in two separate statements:
preprocess_weather >> build_dataset
preprocess_sales >> build_dataset
```
```
# Remaining steps are a single linear chain.
build_dataset >> train_model >> notify
```

### Branching

#### Branching within tasks
```
def _preprocess_sales(**context):
    if context['execution_date'] < ERP_CHANGE_DATE:
        _preprocess_sales_old(**context)
    else
        _preprocess_sales_new(**context)
...
preprocess_sales_data = PythonOperator(
    task_id="preprocess_sales",
    python_callable=_preprocess_sales,
    provide_context=True
)
```  
#### Branching within the DAG
- Building the two sets of tasks is relatively straight-forward: we can simply create tasks for each ERP system separately using the appropriate operators and link the respective tasks together:
```
fetch_sales_old = PythonOperator(...)
preprocess_sales_old = PythonOperator(...)

fetch_sales_new = PythonOperator(...)
preprocess_sales_new = PythonOperator(...)

fetch_sales_old >> preprocess_sales_old
fetch_sales_new >> preprocess_sales_new
```

- Fortunately, Airflow provides built-in support for choosing between sets of downstream tasks using the **BranchPythonOperator**.

```
def _pick_erp_system(**context):
   ...
   
sales_branch = BranchPythonOperator(
    task_id='sales_branch',
    provide_context=True,
    python_callable=_pick_erp_system,
)
```

- we can implement our choice between the two ERP systems by using the callable to return the appropriate task_id depending on the execution date of the DAG:
```
def _pick_erp_system(**context):
   if context["execution_date"] < ERP_SWITCH_DATE:
        return "fetch_sales_old"
    else:
        return "fetch_sales_new"

sales_branch = BranchPythonOperator(
       task_id='sales_branch',
       provide_context=True,
       python_callable=_pick_erp_system,
)

sales_branch >> [fetch_sales_old, fetch_sales_new]
start_task >> sales_branch
[preprocess_sales_old, preprocess_sales_new] >> build_dataset

```

- Trigger rules can be defined for individual tasks using the `trigger_rule` argument, which can be passed to any operator.
- By default, trigger rules are set to `all_success`, meaning that all parents of the corresponding task need to succeed before the task can be run.
- we can change the trigger rule of build_dataset so that it can still trigger if one of its upstream tasks is skipped. One way to achieve this is to change the trigger rule to `none_failed`, which specifies that a task should run as soon as all of its parents are done with executing and none have failed:
```
build_dataset = PythonOperator(
    ...,
    trigger_rule="none_failed",
)
```

- One drawback of this approach is that we now have three edges going into build_dataset. This doesn’t really reflect the nature of our flow, in which we essentially want to fetch sales/weather data (choosing between the two ERP systems first) and then feed these two data sources into build_dataset. For this reason, many people choose to make the branch condition more explicit by adding a dummy task joining the different branches before continuing with the DAG 

![](.README/349eed2e.png)

```
from airflow.operators.dummy_operator import DummyOperator
join_branch = DummyOperator(
    task_id="join_erp_branch",
    trigger_rule="none_failed"
)

[preprocess_sales_old, preprocess_sales_new] >> join_branch
join_branch >> build_dataset
```


### Conditional tasks

- Besides branches, Airflow also provides you with other mechanisms for skipping specific tasks in your DAG depending on certain conditions.
- One way to make conditional notifications is to implement the notification using the PythonOperator and to explicitly check the execution date of the DAG within the notification function:
```
def _notify(**context):
    if context["execution_date"] == ...:
        send_notification()

notify = PythonOperator(
    task_id="notify",
    python_callable=_notify,
    provide_context=True
)
```
- Drawback: the corresponding branching implementation: it confounds the notification logic with the condition, we can no longer use specialised operators (such as a SlackOperator, for example) and tracking of task results in the Airflow UI becomes less explicit 

- Another way to implement conditional notifications is to make the notification task itself conditional, meaning that the actual notification task is only executed based on a predefined condition (in this case whether the DAG run is the most recent DAG run).

```
def _latest_only(**context):
    ...
if_most_recent = PythonOperator(
    task_id="latest_only",
    python_callable=_latest_only,
    provide_context=True,
    dag=dag,
)
if_most_recent >> notify
```

- we need to fill in our _latest_only function to make sure that downstream tasks are skipped if the execution_date does not belong to the most recent run. To do so, we need to 
  - (a) check our execution date and, if required, 
  - (b) raise an AirflowSkipException from our function, which is Airflow’s way of allowing us to indicate that the condition and all its downstream tasks should be skipped, thus skipping the notification.

```
from airflow.exceptions import AirflowSkipException

def _latest_only(**context):
     # Find the boundaries for our execution window.
       left_window = context['dag'].following_schedule(context['execution_date'])
       right_window = context['dag'].following_schedule(left_window)
       
     # Check if our current time is within the window.
     now = pendulum.utcnow()
       if not left_window < now <= right_window:
           raise AirflowSkipException("Not the most recent run!")
```  

- As this is a common use case, Airflow also provides the built-in `LatestOnlyOperator` class, which performs the same task as our custom built implementation based on the PythonOperator.

```
from airflow.operators.latest_only_operator import LatestOnlyOperator

latest_only = LatestOnlyOperator(
    task_id='latest_only',
    dag=dag, 
)

train_model >> if_most_recent >> notify
```

### More about trigger rules
#### What is a trigger rule?
- Trigger rules are essentially the conditions that Airflow applies to tasks to determine whether they are ready to execute, as a function of their dependencies (= preceding tasks in the DAG).
- Airflows default trigger rule is “all_success”, which states that all of a tasks dependencies must have completed successfully before the task itself can be executed.

#### Other trigger rules

|Trigger rule|Behaviour|Example use case|
|------------|---------|----------------|
|all_success (default)|Triggers when all parent tasks have completed successfully.|The default trigger rule for a normal workflow.|
|all_failed|Triggers when all parent tasks have failed (or have failed as a result of a failure in their parents).|Trigger error handling code in situations where you expected at least one success amongst a group of tasks.|
|all_done|Triggers when all parents are done with their execution, regardless of the their resulting state.|Execute clean-up code that you want to execute when all tasks have finished (e.g. shutting down a machine or stopping a cluster).|
|one_failed|Triggers as soon as at least one parent has failed, does not wait for other parent tasks to finish executing.|Quickly trigger some error handling code, such as notifications or rollbacks.|
|one_success|Triggers as soon as one parent succeeds, does not wait for other parent tasks to finish executing.|Quickly trigger downstream computations/notifications as soon as one result becomes available.|
|none_failed|Triggers if no parents have failed, but have either completed successfully or been skipped.|Joining conditional branches in Airflow DAGs|
|none_skipped|Triggers if no parents have been skipped, but have either completed successfully or failed.|?|
|dummy|Triggers regardless of the state of any upstream tasks.|Used for internal testing by Airflow.|


## Triggering workflows

### Polling conditions with sensors
- One common use case to start a workflow is the arrival of new data - imagine a third party delivering a daily dump of its data on a shared storage system between your company and the third party. 
- the daily data often arrives at random times.
- **One way** to solve this in Airflow is with the help of sensors, which are a special type (subclass) of operators. Sensors continuously poll for certain conditions to be true, and succeed if so. If false, the sensor will wait and try again until either the condition is true, or a timeout is eventually reached:
```
from airflow.contrib.sensors.file_sensor import FileSensor

wait_for_supermarket_1 = FileSensor( 
    task_id="wait_for_supermarket_1",
    filepath="/data/supermarket1/data.csv", 
)
```
- This **FileSensor** will check for the existence of /data/supermarket1/data.csv and return True if the file exists. 
- If not, it returns False and the sensor will wait for a given period (default 60 seconds) and try again.

#### Polling custom conditions
- Airflow’s FileSensor does support wildcards to match e.g. data- *.csv, this will match any file matching the pattern.
- Under the hood the FileSensor uses globbing18 to match patterns against file or directory names. While globbing (similar to regex, yet more limited in functionality) would be able to match multiple patterns with a complex pattern, a more readable approach is to implement the two checks with the PythonSensor.
- The PythonSensor is similar to the PythonOperator in the sense that you supply a Python callable (function/method/etc.) to execute.
- The PythonSensor callable is however limited to returning a boolean value; True to indicate the condition is met successfully, False to indicate it is not.

```
from pathlib import Path

from airflow.contrib.sensors.python_sensor import PythonSensor

def _wait_for_supermarket(supermarket_id): 
    supermarket_path = Path("/data/" + supermarket_id) 
    data_files = supermarket_path.glob("data-*.csv") 
    success_file = supermarket_path / "_SUCCESS" 
    return data_files and success_file.exists()

wait_for_supermarket_1 = PythonSensor( 
    task_id="wait_for_supermarket_1", 
    python_callable=_wait_for_supermarket, 
    op_kwargs={"supermarket_id": "supermarket1"}, 
    dag=dag,
)                   
```

- The DAG class has a **concurrency** argument which controls how many simultaneously running tasks are allowed within that DAG.
- In case of error like:
  - ``` occupying 16 tasks, 2 new tasks cannot run, and any other task trying to run is blocked```
  - This behaviour is often referred to as **“sensor deadlock”**.
  - The maximum number of running tasks in the DAG is reached and thus the impact is limited to that DAG, while other DAGs can still run.
  - Once the global Airflow limit of maximum tasks is reached, your entire system is stalled which is obviously very undesirable!
- Solution:
  - The Sensor class takes an argument mode, which can be set to either **“poke”** or **“reschedule”**.
  - By default it’s set to **“poke”**, leading to the blocking behaviour.
    - the sensor task occupies a task slot as long as it’s running. Once in a while it pokes the condition, and then does nothing but still occupies a task slot.
  - The sensor **“reschedule”** mode releases the slot after it has finished poking, so it only occupies the slots while it’s doing actual work. 
  
### Triggering other DAGs
- Splitting your DAG into multiple smaller DAGs where each DAG takes care of part of the total workflow.
- This scenario can be achieved with the **TriggerDagRunOperator**. This operator allows triggering other DAGs, which you can apply for decoupling parts of a workflow:

![](.README/051593ac.png)

- The string provided to the **trigger_dag_id** argument of the **TriggerDagRunOperator** must match the **dag_id** of the DAG to trigger.

#### Backfilling with the TriggerDagRunOperator
- What if you changed some logic in the process_* tasks and wanted to re-run the DAGs from there on ?
  - In a single DAG you could clear the state of the process_* and corresponding downstream tasks.
  - clearing tasks **only** clears tasks within the same DAG! 
  - Tasks downstream of a **TriggerDagRunOperator** in another DAG are not cleared so be well aware of this behaviour.
  
### Starting workflows with REST/CLI
- Using the Airflow CLI, we can trigger a DAG as follows:
  - ```airflow trigger_dag dag1```  or ```airflow dags trigger dag1```
- Passing context variable in DAG
  - ```airflow trigger_dag dag1 -c ‘{“supermarket_id”: 1}’```
  
- It is also possible to use the REST API for the same result,
  - ```curl localhost:8080/api/experimental/dags/print_dag_run_conf/dag_runs -d {}``` or
  - ```curl localhost:8080/api/experimental/dags/print_dag_run_conf/dag_runs -d '{"conf":{"supermarket": 1}}'```
  