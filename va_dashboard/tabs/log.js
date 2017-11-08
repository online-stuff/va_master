var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
//var DatePicker = require('react-datepicker').default;
var DateRangePicker = require('react-dates').DateRangePicker;
var moment = require('moment');
var Reactable = require('reactable');

var Log = React.createClass({
    getInitialState: function () {
        var checked = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"];
        return {
            logs: [],
            value: "",
            checked: checked
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
        var msg = {
            from_date: startDate,
            to_date: endDate
        };
        this.ws.send(JSON.stringify(msg));
    },
    changeTable: function(checked){
        this.setState({checked: checked});
    },
    render: function () {
        var TableRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Table);
        var DateRangeRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(DateRange);
        var me = this;
        var logs = this.state.logs.filter(function(l){
            if(me.state.checked.indexOf(l.severity) > -1) return true;
            return false;
        });
        return (
            <div id="log-page">
                <DateRange updateLogs={this.updateLogs} />
                <div id='filter-log'>
                    <FilterBtns changeTable={this.changeTable} />
                    <input type='text' placeholder='Search...' value={this.state.value} onChange={this.filter} className='pull-right'/>
                </div>
                <TableRedux logs={logs} filterBy={this.state.value} checked={this.state.checked}/>
            </div>
	);
    }
});

var DateRange = React.createClass({
    getInitialState: function () {
        return {
            startDate: moment().subtract(1, 'days'),
            endDate: moment(),
            focusedInput: null
        }
    },
    handleChange: function(obj) {
        this.setState({
            startDate: obj.startDate,
            endDate: obj.endDate
        });
        this.props.updateLogs(obj.startDate.format('YYYY-MM-DD'), obj.endDate.format('YYYY-MM-DD'));
    },

    focusChange: function(focusedInput){
        this.setState({focusedInput: focusedInput});
    },

    btnClick: function(){
        this.props.updateLogs(this.state.startDate.format('YYYY-MM-DD'), this.state.endDate.format('YYYY-MM-DD'));
    },
    render: function () {
        return (
            <DateRangePicker
                displayFormat="DD/MM/YYYY"
                startDate={this.state.startDate}
                endDate={this.state.endDate}
                onDatesChange={this.handleChange}
                focusedInput={this.state.focusedInput}
                onFocusChange={this.focusChange}
                isOutsideRange={function(){return false}}
            />
        );
    }
});

var FilterBtns = React.createClass({
    getInitialState: function () {
        var severities = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"];
        return {
            severities: severities,
            values: Object.assign([], severities)
        }
    },

	onChange: function (values) {
        this.setState({values: values});
        this.props.changeTable(values);
	},

    render: function () {
        var me = this;
		var btns = this.state.severities.map(function(val){
			return <Bootstrap.ToggleButton key={val} value={val}>{val}</Bootstrap.ToggleButton>;
		});
		return (
            <Bootstrap.ToggleButtonGroup type="checkbox" value={this.state.values} onChange={this.onChange}>
			    {btns}
            </Bootstrap.ToggleButtonGroup>
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
        var logs = this.props.logs.map(function(log, index) {
            var msg = log.message, className = "";
            try{
                var log_json = JSON.parse(msg);
                msg = msg.function;
            }catch (e){
                console.log("JSON error ", index.toString());
                console.log(log.message);
            }
            if(this.state.selected_log.timestamp === log.timestamp)
                className = "info";
            return (
                <Reactable.Tr key={log.timestamp} id={log.timestamp} className={className} onClick={this.rowSelected}>
                    <Reactable.Td column="Timestamp">{log.timestamp.substring(0,19)}</Reactable.Td>
                    <Reactable.Td column="Message">{msg}</Reactable.Td>
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
            <Reactable.Table className="table striped tbl-select" columns={columns} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={columns} filterBy={this.props.filterBy} hideFilterInput>
                {logs}
            </Reactable.Table>
            <div className="selected-block">
                <label>Log Details</label>
                {selected_log}
            </div>
        </div> );
    }
});


Log = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Log);

module.exports = Log;
