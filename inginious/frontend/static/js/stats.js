window.onload = function() {
    var ctx = document.getElementById('canvas').getContext('2d');
    window.myLine = new Chart(ctx, config);
};
window.resetZoom = function() {
    window.myLine.resetZoom();
};

$("#diag2").click(function () {
    diagram_request("diag1");
})

$("#diag3").click(function () {
    diagram_request("diag2");
})

/**
     *
     * Helpers
     *
     */
    const reducer = (accumulator, currentValue) => accumulator + currentValue;
    function mean(table,labels){
        if (table.length === 0){
            return 0
        }else{
            let sumnote = 0;
            let i=0
            while (i< table.length){
                sumnote+= labels[i]*table[i];
                i++;
            }
            let nstudents = table.reduce(reducer);
            return Math.round((sumnote/nstudents)*2)*0.5;
        }
    }
    function standard_deviation(table,labels, mean){
        let result;
        let sub_sum =0;
        let i=0;
        while(i<table.length){
            let j=1;
            while (j <= table[i]){
                let val = Math.pow(Math.abs(labels[i]-mean),2);
                sub_sum+=val;
                j++;
            }
            i++;
        }
        let nstudents = table.reduce(reducer);
        result = sub_sum/nstudents;
        return Math.sqrt(result);
    }

    /**
     *
     * Requests
     *
     */

    function diagram_request(name) {
      const url = window.location.href +"/"+ name;
      $.ajax({
        url: url,
        data: {
          "student_ids": localStorage.getItem("students"),
          "task_ids": localStorage.getItem("tasks")
        },
        type: "GET",
        success: function (result) {
          let json_result = JSON.parse(result);
          if (name ==="diag1"){
            for (const [title,subdict] of Object.entries(json_result["stud_per_grad"])){
              $("#menu1").append("<canvas id='canvas_"+title+"'></canvas>");
              display_diagram_1(subdict,title,json_result["task_titles"][title]);
            }

          }else if (name === "diag2"){
            display_diagram_2(json_result);
          }else {
            console.log("none");
          }

        },
        error: function (error) {
          console.log("ERROR - " + error);
        }
      })
    }
     /**
     *
     * Displays of the histogram
     *
     */
    function display_diagram_1(table_stud_per_note,canvas_name,title){

        //initialisation
        var values = new Array(40);
        values.fill(0);
        //This is to pass percentage to /20 value
        for (const [key, value] of Object.entries(table_stud_per_note)) {
          values[(key)*2] = value;
        }
        var labels = [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11,11.5,12,12.5,13,13.5,14,14.5,15,15.5,16,16.5,17,17.5,18,18.5,19,19.5,20];
        var m = mean(values,labels);
        var sd = standard_deviation(values,labels,m);
        sd = Math.round(sd*2)*0.5;
        var b1 = m-sd;
        var b2 = m+sd;
        if(b1 < 0){
          b1=0;
        }
        if(b2 > 20){
          b2=20;
        }
        var dat =[{x:b1,y:10},{x:b2,y:10}];
        var lines = [
                      {
						type: 'line',
                        label:{content:'Mean',enabled:true,fontColor: "#000",backgroundColor:'red',cornerRadius: 0,position:"bottom"},
						mode: 'vertical',
						scaleID: 'x-axis-label',
						value: m,
						borderColor: 'red',
						borderWidth: 1,

                      }
                    ];


        var ctx = document.getElementById('canvas_'+canvas_name).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                datasets: [{
                    label: 'StudentPerNote',
                    data: values
                },{
                    type: 'line',
                    label:'StandardDeviation',
                    data: dat,
                    mode :'horizontal',
                    scaleID:'x-axis-label',
                    backgroundColor:'lightblue',
                }
              ],
                labels: labels
            },
            options:{
                title: {
                  display: true,
                  text: title
                },
                responsive: true,
                scales: {
                    xAxes: [{
                        id : 'x-axis-label',
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Note'
                        }
                    }],
                    yAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Students'
                        },
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                },
                annotation: {
                    drawTime: 'afterDatasetsDraw',
                    events : ["click"],
                    annotations: lines
                  }
            },
        });
    }


function display_diagram_2(table_per_task){
      let nstuds =table_per_task["stud_per_grad"]["nstuds"];
      let task_ids =localStorage.getItem("tasks").split(",");
      let viewed =[];
      let attempted = [];
      let succeeded = [];
      let title_text = table_per_task["task_titles"];
      for (let task_id of task_ids){
          if (table_per_task["stud_per_grad"][task_id].length > 0 ){
              viewed.push(table_per_task["stud_per_grad"][task_id][0]["viewed"]);
              attempted.push(table_per_task["stud_per_grad"][task_id][0]["attempted"]);
              succeeded.push(table_per_task["stud_per_grad"][task_id][0]["succeeded"]);
          }else{
              viewed.push(0);
              attempted.push(0);
              succeeded.push(0);
          }

      }

      var line = [
                      {
						type: 'line',
                        label:{content:'Total Students',enabled:true,fontColor: "#000",backgroundColor:'red',cornerRadius: 0,position:"bottom"},
						mode: 'horizontal',
						scaleID: 'y-axis-label',
						value: nstuds,
						borderColor: 'red',
						borderWidth: 1,

                      }
                    ];

      var ctx = document.getElementById('myChart2').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                datasets: [
        {
            label: "Viewed",
            backgroundColor: "blue",
            data: viewed
        },
        {
            label: "Attempted",
            backgroundColor: "red",
            data: attempted
        },
        {
            label: "Succeeded",
            backgroundColor: "green",
            data: succeeded
        }
    ],
                labels: title_text
            },
            options:{
                responsive: true,
                scales: {
                    xAxes: [{
                        id : 'x-axis-label',
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Tasks'
                        },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 90,
                            minRotation: 90
                        }
                    }],
                    yAxes: [{
                      id : 'y-axis-label',
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: ' #Students'
                        },
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                },
                annotation: {
                    drawTime: 'afterDatasetsDraw',
                    events : ["click"],
                    annotations: line
                  }
            },
        });
    }