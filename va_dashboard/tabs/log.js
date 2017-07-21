var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var DatePicker = require('react-datepicker').default;
var moment = require('moment');
var Reactable = require('reactable');

var Log = React.createClass({
    getInitialState: function () {
        return {
            logs: [],
            value: ""
        }
    },
    initLog: function () {
        var host = window.location.host;
        if(host.indexOf(":") == 0){
            host += ":80";
        }
        var protocol =  window.location.protocol === "https:" ? "wss" : "ws";
        this.ws = new WebSocket(protocol  +"://"+ host +"/log");
        var me = this;
        this.ws.onmessage = function (evt) {
            var data = JSON.parse(evt.data);
            var logs = [];
            if(data.type === "update")
                logs = me.state.logs.concat([data.message]);
            else if(data.type === "init")
                logs = data.logs;
            me.setState({logs: logs});
        };
        this.ws.onerror = function(evt){
            me.ws.close();
            me.props.dispatch({type: 'SHOW_ALERT', msg: "Socket error."});
        };
    },
    componentDidMount: function () {
        if(!this.props.alert.show)
            this.initLog();
    },
    close_socket: function () {
        this.ws.close();
    },
    filter: function (evt) {
        this.setState({value: evt.target.value});
    },
    updateLogs: function(startDate, endDate){
        console.log(startDate, endDate);
        var msg = {
            from_date: startDate,
            to_date: endDate
        };
        this.ws.send(JSON.stringify(msg));
    },
    render: function () {
        var TableRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Table);
        var DateRangeRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(DateRange);
        return (
            <div>
                <DateRange updateLogs={this.updateLogs} />
                <input type='text' value={this.state.value} onChange={this.filter} />
                <TableRedux logs={this.state.logs} filterBy={this.state.value} />
	    </div>
	);
    }
});

var DateRange = React.createClass({
    getInitialState: function () {
        return {
            startDate: moment().subtract(1, 'days'),
            endDate: moment()
        }
    },
    handleChangeStart: function(date) {
        this.setState({
            startDate: date
        });
    },

    handleChangeEnd: function(date) {
        this.setState({
            endDate: date
        });
    },
    btnClick: function(){
        this.props.updateLogs(this.state.startDate.format('YYYY-MM-DD'), this.state.endDate.format('YYYY-MM-DD'));
    },
    render: function () {
        return (
            <div className="date-range">
                <DatePicker
                    dateFormat="DD/MM/YYYY"
                    selected={this.state.startDate}
                    selectsStart
                    startDate={this.state.startDate}
                    endDate={this.state.endDate}
                    onChange={this.handleChangeStart}
                />
                <DatePicker
                    dateFormat="DD/MM/YYYY"
                    selected={this.state.endDate}
                    selectsEnd
                    startDate={this.state.startDate}
                    endDate={this.state.endDate}
                    onChange={this.handleChangeEnd}
                />
                <Bootstrap.Button onClick={this.btnClick}>Update logs</Bootstrap.Button>
	   </div>
        );
    }
});

var Table = React.createClass({
    getInitialState: function () {
        return {
            selected_log: {}
        }
    },

    rowSelected: function(evt) {
        var selected_row = this.props.logs.find(function(log){
            return log.timestamp === evt.currentTarget.id;
        });
        var selected_row = Object.assign({}, selected_row);
        var msg = JSON.parse(selected_row['message']);
        selected_row['message'] = msg;
        selected_row['message']['method'] = msg['data']['method'];
        delete selected_row['message']['data'];
        this.setState({selected_log: selected_row});
    },

    render: function () {
        var logs = this.props.logs.map(function(log) {
            var msg = JSON.parse(log.message), className = "";
            if(this.state.selected_log.timestamp === log.timestamp)
                className = "info";
            return (
                <Reactable.Tr key={log.timestamp} id={log.timestamp} className={className} onClick={this.rowSelected}>
                    <Reactable.Td column="Timestamp">{log.timestamp.substring(0,19)}</Reactable.Td>
                    <Reactable.Td column="Message">{msg.function}</Reactable.Td>
                    <Reactable.Td column="Severity">{log.severity}</Reactable.Td>
                    <Reactable.Td column="Host">{log.host}</Reactable.Td>
                    <Reactable.Td column="Facility">{log.facility}</Reactable.Td>
                </Reactable.Tr>
            );
        }.bind(this));
        var selected_log = [];
        if("message" in this.state.selected_log){
            var msg = this.state.selected_log.message;
            //msg['method'] = JSON.parse(msg['data'])[;
            for(var key in msg){
                var div = (<div key={key}><b>{key}:</b> {msg[key].toString()}</div>);
                selected_log.push(div);
            }
        }
        var columns = ["Timestamp", "Message", "Severity", "Host", "Facility"];
        return ( <div>
            <Reactable.Table className="table striped tbl-block tbl-select" columns={columns} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={columns} filterBy={this.props.filterBy} hideFilterInput>
                {logs}
            </Reactable.Table>
            <div className="selected-block">
                {selected_log}
            </div>
        </div> );
    }
});


Log = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Log);

module.exports = Log;
