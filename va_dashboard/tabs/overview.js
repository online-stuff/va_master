var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Chart = require("react-chartjs-2").Chart;
var DoughnutChart = require("react-chartjs-2").Doughnut;
var defaults = require("react-chartjs-2").defaults;
var Bootstrap = require('react-bootstrap');

defaults.global.legend.display = false;

Chart.pluginService.register({
    beforeDraw: function(chart) {
        var width = chart.chart.width,
            height = chart.chart.height,
            ctx = chart.chart.ctx;

        ctx.restore();
        var fontSize = (height / 114).toFixed(2);
        ctx.font = fontSize + "em sans-serif";
        ctx.textBaseline = "middle";

        var allData = chart.data.datasets[0].data;
        var total = 0;

        for (var i in allData) {
            total += allData[i];
        }
        var percentage = Math.round(((total - allData[allData.length-1]) / total) * 100);

        var text = percentage.toString() + "%",
            textX = Math.round((width - ctx.measureText(text).width) / 2),
            textY = height / 1.2;

        ctx.fillText(text, textX, textY);
        ctx.save();
    }
});

var Overview = React.createClass({
    getInitialState: function () {
        return {hosts: []};
    },
    componentWillMount() {
        this.getHosts();
	},
    getHosts: function(){
        var data = {hosts: []};
        Network.post('/api/hosts/info', this.props.auth.token, data).done(function(data) {
            this.setState({hosts: data});
        }.bind(this));
    },
    render: function() {
        var appblocks;
        // var appblocks = [['Directory', 'fa-group'], ['Monitoring', 'fa-heartbeat'],
        //     ['Backup', 'fa-database'], ['OwnCloud', 'fa-cloud'], ['Fileshare', 'fa-folder-open'],
        //     ['Email', 'fa-envelope']];
        // appblocks = appblocks.map(function(d){
        //     return (
        //         <div key={d[0]} className='app-block'>
        //             <div className='icon-wrapper'>
        //                 <i className={'fa ' + d[1]} />
        //             </div>
        //             <div className='name-wrapper'>
        //                 <h1>{d[0]}</h1>
        //             </div>
        //             <div className='clearfix' />
        //         </div>
        //     );
        // });
        var HostRedux = connect(function(state){
            return {auth: state.auth};
        })(Host);
        var LogRedux = connect(function(state){
            return {auth: state.auth};
        })(Log);
        var host_rows = this.state.hosts.map(function(host) {
            return <HostRedux key={host.hostname} title={host.hostname} chartData={host.instances} instances={host.instances.length} host_usage={host.host_usage} />;
        }.bind(this));
        return (
            <div>
                <div className="graph-block">
                    {host_rows}
                </div>
                <LogRedux />
                <div className="appblock">
                    {appblocks}
                    <div style={{clear: 'both'}} />
                </div>
            </div>);
    }
});

var Host = React.createClass({
    getInitialState: function () {
        var cpuData = [], ramData = [], diskData = [];
        var instances = this.props.chartData.map(function(instance) {
            cpuData.push(instance.used_cpu);
            ramData.push(instance.used_ram);
            diskData.push(instance.used_disk);
            return instance.hostname;
        });
        instances.push("Free");
        var usage = this.props.host_usage;
        cpuData.push(usage.free_cpus);
        ramData.push(usage.free_ram);
        diskData.push(usage.free_disk);
        var data = [cpuData, ramData, diskData];
        var colors = this.getRandomColors(instances.length+1);
        return {
            chartData: data,
            labels: instances,
            colors: colors,
        };
    },

    getRandomColors: function(count) {
        var letters = '0123456789ABCDEF'.split('');
        var colors = [];
        for(var j = 0; j < count; j++){
            var color = '#';
            for (var i = 0; i < 6; i++ ) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            colors.push(color);
        }
        return colors;
    },
    render: function() {
        var DoughnutRedux = connect(function(state){
            return {auth: state.auth};
        })(DoughnutComponent);
        return (
            <div>
                <Bootstrap.PageHeader>{this.props.title}</Bootstrap.PageHeader>
                <div>
                    <DoughnutRedux data={this.state.chartData[0]} labels={this.state.labels} colors={this.state.colors} title="CPU" />
                    <DoughnutRedux data={this.state.chartData[1]} labels={this.state.labels} colors={this.state.colors} title="MEMORY"  />
                    <DoughnutRedux data={this.state.chartData[2]} labels={this.state.labels} colors={this.state.colors} title="STORAGE"  />
                    <label>Instances: {this.props.instances}</label>
                </div>
            </div>
        );
    }
});

var DoughnutComponent = React.createClass({
    getInitialState: function () {
        return {chartOptions: {
                    maintainAspectRatio: false, title: {
                        display: true,
                        text: this.props.title
                    },
                    cutoutPercentage: 70,
                    rotation: 1 * Math.PI,
                    circumference: 1 * Math.PI
                }, chartData: {
                    labels: this.props.labels,
                    datasets: [
                        {
                            data: this.props.data,
                            backgroundColor: this.props.colors,
                            hoverBackgroundColor: this.props.colors
                        }]
                }};
            },
    render: function() {
        return (
            <div className="chart">
                <DoughnutChart data={this.state.chartData} options={this.state.chartOptions}/>
            </div>
        );
    }
});

var Log = React.createClass({
    getInitialState: function () {
        var ws = new WebSocket("ws://192.168.80.39:8888/sockets/log_monitor");
        ws.onopen = function() {
            ws.send("Hello, world");
        };
        ws.onmessage = function (evt) {
            alert(evt.data);
        };
        return {logs: [
            ]
        }
    },
    render: function() {
        var log_rows = this.state.logs.map(function(log, i) {
            return (
                <div key={i}>{log.description}</div>
            );
        }.bind(this));
        return (
            <div className="log-block">
                <Bootstrap.PageHeader>Log</Bootstrap.PageHeader>
                {log_rows}
            </div>
        );
    }
});

Overview = connect(function(state) {
    return {auth: state.auth};
})(Overview);

module.exports = Overview;
