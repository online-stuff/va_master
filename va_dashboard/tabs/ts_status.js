var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Chart = require("react-chartjs-2").Chart;
var DoughnutChart = require("react-chartjs-2").Doughnut;
var BarChart = require("react-chartjs-2").Bar;
var defaults = require("react-chartjs-2").defaults;
var Bootstrap = require('react-bootstrap');

var Ts_status = React.createClass({
    componentWillUnmount: function () {
        this.refs.log.getWrappedInstance().close_socket();
    },
    render: function() {
        var TsBlockRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Ts_block);
        var LogRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(Log);
        return (
            <div>
                <TsBlockRedux />
                <LogRedux ref="log" />
            </div>
        );
    }
});

var Ts_block = React.createClass({
    getInitialState: function () {
        defaults.global.legend.display = false;
        return {ts: [], loading: true};
    },
    componentWillMount() {
        this.getTS();
        var me = this;
        this.interval = setInterval(function(){
            me.getTS();
        }, 15000);
    },
    componentWillUnmount() {
        clearInterval(this.interval);
    },
    getTS: function(){
        var me = this;
        Network.get('/api/panels/ts_data', this.props.auth.token).done(function(data) {
            me.setState({ts: data['va-monitoring.evo.mk'], loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            //clearInterval(this.interval);
        });
    },
    render: function() {
        var TSRedux = connect(function(state){
            return {auth: state.auth};
        })(TS);
        var ts_rows = Object.keys(this.state.ts).map(function(key) {
            return <TSRedux key={key} title={key} chartData={this.state.ts[key]} />;
        }.bind(this));
        const spinnerStyle = {
            display: this.state.loading ? "block": "none",
        };
        return (
                <div className="graph-block">
                    <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                    {ts_rows}
                </div>
            );
    }
});

var TS = React.createClass({
    getInitialState: function () {
        var colors1 = this.getColors('cpu');
        var colors2 = this.getColors('memory');
        var colors3 = this.getColors('users');
        return {
            colors: [colors1, colors2, colors3]
        };
    },
    getColors: function(type) {
        var colors = {'green': '#4bae4f','red': '#fe5151','free': '#d3d3d3'};
        var resColors = [];
        if(this.props.chartData['status'][type]['state'] == "OK"){
            resColors.push(colors.green);
        }else{
            resColors.push(colors.red);
        }
        resColors.push(colors.free);
        return resColors;
    },
    render: function() {
        var DoughnutRedux = connect(function(state){
            return {auth: state.auth};
        })(DoughnutComponent);
        mem_util = this.props.chartData['data']['Physical Memory Utilisation'];
        cpu_util = this.props.chartData['data']['Avg Utilisation CPU_Total'];
        return (
            <Bootstrap.Panel header={this.props.title} bsStyle='primary'>
                <div className="flex-box">
                <DoughnutRedux height={200} data={[cpu_util, 100-cpu_util]} innerData={this.props.chartData['data']['CPU Count']} status={this.props.chartData['status']['cpu']['output']} labels={['Avg Utilisation CPU_Total', 'Free CPU']} colors={this.state.colors[0]} title="CPU" />
                <DoughnutRedux height={200} data={[mem_util, 100-mem_util]} innerData={this.props.chartData['data']['Physical Memory Total']} status={this.props.chartData['status']['memory']['output']} labels={['Physical Memory Utilisation', 'Free Memory']} colors={this.state.colors[1]} title="MEMORY"  />
                <DoughnutRedux height={200} data={[this.props.chartData['data']['ActiveSessions'], this.props.chartData['data']['InactiveSessions']]} status={this.props.chartData['status']['users']['output']} labels={['ActiveSessions', 'InactiveSessions']} colors={this.state.colors[2]} title="USERS"  />
                </div>
            </Bootstrap.Panel>
        );
    }
});

var DoughnutComponent = React.createClass({
    getInitialState: function () {
        var data = {chartOptions: {
                    title: {
                        display: true,
                        text: this.props.title
                    },
                    cutoutPercentage: 70
                }, chartData: {
                    labels: this.props.labels,
                    datasets: [
                        {
                            data: this.props.data,
                            backgroundColor: this.props.colors,
                            hoverBackgroundColor: this.props.colors
                        }]
                }};
        if('innerData' in this.props){
            data.chartOptions.customInnerData = this.props.innerData;
        }
        return data;
    },
    render: function() {
        return (
            <div className="chart1">
                <DoughnutChart data={this.state.chartData} options={this.state.chartOptions}/>
                <div className="chart-status">{this.props.status}</div>
            </div>
        );
    }
});

var Log = React.createClass({
    getInitialState: function () {
        return {logs: [], category: ['info', 'warning', 'danger'] }
    },
    componentDidMount: function () {
        var host = window.location.host;
        if(host.indexOf(":") == 0){
            host += ":80";
        }
        var protocol =  window.location.protocol === "https:" ? "wss" : "ws";
        this.ws = new WebSocket(protocol  +"://"+ host +"/log");
        var me = this;
        this.ws.onmessage = function (evt) {
            var data = JSON.parse(evt.data), result = [];
            if(Array.isArray(data)){
                result = data.filter(function(d) {
                    if(d.length > 0){
                        return true;
                    }
                    return false;
                }).map(function(d) {
                    return JSON.parse(d);
                });
            }else if(typeof data === "string"){
                try {
                    result = [JSON.parse(data)];
                } catch(e) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: "Log has invalid format."});
                }
            }else{
                me.props.dispatch({type: 'SHOW_ALERT', msg: "Log has invalid format."});
            }
            if(result.length > 0){
                var logs = result.reverse().concat(me.state.logs).filter(function(log){
                    var msg = JSON.parse(log.message);
                    if(typeof msg.path === 'string' && (msg.path.indexOf('apps') > -1 || msg.path.indexOf('triggers') > -1 && msg.data.method == 'post')){
                        return true;
                    }
                    return false;
                });
                me.setState({logs: logs});
            }
        };
        this.ws.onerror = function(evt){
            me.props.dispatch({type: 'SHOW_ALERT', msg: "Socket error."});
            this.close_socket();
        };
    },
    close_socket: function () {
        this.ws.close();
    },
    render: function() {
        var times = [], currentDate = new Date(); //"2017-02-21T14:00:14+00:00"
        var prevHourTs = currentDate.setHours(currentDate.getHours()-1);
        var logs = this.state.logs;
        var datasets = [{
            label: 'info',
            data: [],
            backgroundColor: "#31708f",
            borderColor: "#31708f"
        }, {
            label: 'warning',
            data: [],
            backgroundColor: "#ffa726",
            borderColor: "#ffa726"
        }, {
            label: 'danger',
            data: [],
            backgroundColor: "#a94442",
            borderColor: "#a94442"
        }];
        if(logs.length > 0){
            var prev_log = logs[0];
        }
        var logs_limit = 10, brojac=0, log_rows = [];
        for(var i=0; i<logs.length; i++){
            log = logs[i];
            var logClass = log.severity == "warning" ? "text-warning" : (log.severity == "err" || log.severity == "critical" || log.severity == "emergency") ? "text-danger" : "text-info";
            var timestamp = new Date(log.timestamp);
            if(timestamp.getTime() > prevHourTs){
                var logLabel = logClass.split('-')[1];
                var prevTimestamp = new Date(prev_log.timestamp);
                var category = this.state.category;
                // groups logs with same hh:mm for the graph
                if(i > 0 && timestamp.getHours() == prevTimestamp.getHours() && timestamp.getMinutes() == prevTimestamp.getMinutes()){
                    var index = category.indexOf(logLabel);
                    datasets[index].data[datasets[index].data.length - 1] += 1;
                }else{
                    times.push(timestamp);
                    for(j=0; j<category.length; j++){
                        if(category[j] == logLabel){
                            datasets[j].data.push(1);
                        }else{
                            datasets[j].data.push(0);
                        }
                    }
                }
                if(i > 0){
                    prev_log = log;
                }
            }
            if(brojac < logs_limit){
            var hour = timestamp.getHours();
            var min = timestamp.getMinutes();
            var sec = timestamp.getSeconds();
            var message = JSON.parse(log.message), msg = "";
            for(var key in message){
                if(typeof message[key] === 'object'){
                    msg += message[key].method + " ";
                }else{
                    msg += message[key] + " ";
                }
            }
            log_rows.push (
                <div key={i} className={"logs " + logClass}>{timestamp.toISOString().slice(0, 10) + " " + hour + ":" + min + ":" + sec + ", " + message.user + ", " + log.host + ", " + log.severity + ", " + message.path + ", " + msg}</div>
            );
            }
            brojac++;
        }
        var LogChartRedux = connect(function(state){
            return {auth: state.auth};
        })(LogChart);
        return (
            <Bootstrap.Panel header='Logs' bsStyle='primary' className="log-block">
                <LogChartRedux datasets={datasets} labels={times} minDate={currentDate} />
                {log_rows}
            </Bootstrap.Panel>
        );
    }
});

var LogChart = React.createClass({
    getInitialState: function () {
        var maxDate = new Date();
        var maxDateTs = maxDate.setMinutes(maxDate.getMinutes() + 1);
        return {chartOptions: {
                    maintainAspectRatio: false,
                    responsive: true,
                    scales: {
                        xAxes: [{
                            type: 'time',
                            stacked: true,
                            display: false,
                            categoryPercentage: 1.0,
                            barPercentage: 1.0,
                            time: {
                                displayFormats: {
                                    minute: 'HH:mm',
                                    hour: 'HH:mm',
                                    second: 'HH:mm:ss',
                                },
                                tooltipFormat: 'DD/MM/YYYY HH:mm',
                                unit: 'minute',
                                unitStepSize: 0.5,
                                min: this.props.minDate,
                                max: maxDateTs
                            },
                            gridLines: {
                                display:false
                            }
                        }],
                        yAxes: [{
                            display: false,
                            stacked: true,
                            gridLines: {
                                display:false
                            }
                        }]
                    }
                }, chartData: {
                    labels: this.props.labels,
                    datasets: this.props.datasets
                }};
    },
    componentDidMount: function () {
        var me = this;
        this.intervalId = setInterval(function(){
            var chartOptions = me.state.chartOptions;
            var mindate = new Date(chartOptions.scales.xAxes[0].time.min);
            var maxdate = new Date(chartOptions.scales.xAxes[0].time.max);
            mindate.setMinutes(mindate.getMinutes() + 1);
            maxdate.setMinutes(maxdate.getMinutes() + 1);
            chartOptions.scales.xAxes[0].time.min = mindate;
            chartOptions.scales.xAxes[0].time.max = maxdate;
            me.setState({chartOptions: chartOptions});
        }, 60000);
    },
    componentWillUnmount: function() {
        clearInterval(this.intervalId);
    },
    render: function() {
        return (
            <div className="log-chart">
                <BarChart data={this.state.chartData} options={this.state.chartOptions} redraw />
            </div>
        );
    }
});

Ts_status = connect(function(state) {
    return {auth: state.auth};
})(Ts_status);

module.exports = Ts_status;

