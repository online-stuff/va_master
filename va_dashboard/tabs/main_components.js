import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
import { findDOMNode } from 'react-dom';
var components = require('./basic_components');
import { Table as Reactable, Tr, Th, Thead, Td } from 'reactable';
import { hashHistory } from 'react-router';
import { Line, Pie, Bar, defaults } from "react-chartjs-2";
var moment = require('moment');
import { DateRangePicker, SingleDatePicker } from 'react-dates';
import { getRandomColor, getRandomColors, getReduxComponent, getModalHeader, getModalFooter, download } from './util';
import Select from 'react-select';

const Div = (props) => {
    let redux = {};
    let { elements, classNames, div } = props;
    let divElements = elements.map(function(element) {
        let { name, type, reducers } = element;
        element.key = name;
        redux[type] = getReduxComponent(components[type], reducers);
        let Redux = redux[type];
        return React.createElement(Redux, element);
    });
    if(div){
        classNames += ' ' + div.show;
    }
    return (
        <div className={classNames}>
            {divElements}
        </div>
    );
}

const MultiTable = (props) => {
    let redux = {}, tables = [];
    for(let x in props.table){
        if(x !== "path"){
            let elements = props.elements.map((element) => {
                let { type, reducers } = element;
                element.name = x;
                element.key = type + element.name;
                redux[type] = getReduxComponent(components[type], element.reducers);
                var Redux = redux[type];
                return React.createElement(Redux, element);
            });
            tables.push(elements);
        }
    }
    return (
        <div className="multi">
            {tables}
        </div>
    );
}

class Chart extends Component {
    constructor (props) {
        super(props);
        defaults.global.legend.display = true;
        defaults.global.legend.position = 'right';
        var chartData = this.getData(this.props.data, false);
        this.state = {chartOptions: {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                xAxes: [{
                    type: 'time',
                    stacked: true,
                    time: {
                        displayFormats: {
                            year: 'YYYY-MM-DD',
                            quarter: 'YYYY-MM-DD',
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            second: 'HH:mm:ss'
                        },
                        tooltipFormat: 'DD/MM/YYYY HH:mm'
                        //unit: 'minute',
                        //unitStepSize: 5
                    }
                }],
                yAxes: [{
                    stacked: true
                }]
            }
        }, chartData};
        this.getData = this.getData.bind(this);
        this.btn_click = this.btn_click.bind(this);
    }
    getData(data, check) {
        var datasets = [], times = [], chartData = {}, prevColors = {};
        if(check){
            for(let i=0; i < this.state.chartData.datasets.length; i++) {
                let dataset = this.state.chartData.datasets[i];
                prevColors[dataset.label] = dataset.backgroundColor;
            }
        }
        for(var key in data){
            var obj = {}, prevColor = prevColors[key];
            var color = prevColor || getRandomColor();
            obj.label = key;
            obj.data = [];
            var chart_data = data[key];
            for(let i=0; i<chart_data.length; i++){
                obj.data.push(chart_data[i].y);
            }
            obj.backgroundColor = color;
            obj.borderColor = color;
            datasets.push(obj);
        }
        for(let i=0; i<data[key].length; i++){
            times.push(data[key][i].x * 1000);
        }
        chartData.labels = times;
        chartData.datasets = datasets;
        return chartData;
    }
    btn_click (period, interval, unit, step) {
        let server_name = this.props.panel.server;
        let { provider, service } = this.props;
        let data = {server_name, args: [provider, service, period, interval]};
        Network.post('/api/panels/chart_data', this.props.auth.token, data).done(d => {
            let chartOptions = Object.assign({}, this.state.chartOptions);
            chartOptions.scales.xAxes[0].time.unit = unit;
            chartOptions.scales.xAxes[0].time.unitStepSize = step;
            this.setState({chartData: this.getData(d[server_name], true), chartOptions});
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }
    render () {
        let { chartData, chartOptions } = this.state;
        return (
            <div>
                <div className="panel_chart">
                    <Line name="chart" height={200} data={chartData} options={chartOptions} redraw />
                </div>
                <div id="chartBtns">
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1h", "300", 'minute', 5)}>Last hour</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-5h", "1500", 'hour', 1)}>Last 5 hours</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1d", "7200", 'hour', 4)}>Last day</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-7d", "86400", 'day', 1)}>Last week</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1m", "86400", 'day', 5)}>Last month</button>
                </div>
            </div>
        );
    }
}

class Table extends Component {
    btn_clicked(id, evtKey){
        var checkPath = 'path' in this.props.table && this.props.table.path.length > 0;
        if(!checkPath && 'args' in this.props.panel && this.props.panel.args !== ""){
            id.unshift(this.props.panel.args);
        }
        if(checkPath){
            var args = [this.props.table.path[0]]
            if(this.props.table.path.length > 1){
                args.push(this.props.table.path[1]);
                var rest = this.props.table.path.slice(2,);
                var path = "", slash = rest.length > 0 ? '/' : '';
                for(var i=1; i<rest.length; i++){
                    path += rest[i];
                }
                if(slash)
                    args.push(rest[0]);
                args.push(path + slash + id[0]);
            }else{
                args.push(id[0]);
            }
            var data = {"server_name": this.props.panel.server, "action": evtKey, "args": args};
            if(typeof evtKey === 'object' && evtKey.type === "download"){
                data.action = evtKey.name;
                data['url_function'] = 'get_backuppc_url';
                download('/api/panels/serve_file_from_url', this.props.auth.token, data, id[0], (msg) => {
                    this.props.dispatch({type: 'SHOW_ALERT', msg});
                });
            }else{
                Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
                    if(typeof msg === 'string'){
                        this.props.dispatch({type: 'SHOW_ALERT', msg});
                    }
                }).fail(msg => {
                    this.props.dispatch({type: 'SHOW_ALERT', msg});
                });
            }
        }else if(evtKey == 'chart'){
            var newName = this.props.name.replace(/\s/g, "_");
            var newId = id[0].replace(/:/g, "_");
            newId = newId.replace(/\s/g, "_");
            hashHistory.push('/chart_panel/' + this.props.panel.server + '/' + newName + '/' + newId);
        }else if('modals' in this.props && evtKey in this.props.modals){
            if("readonly" in this.props){
                var rows = this.props.table[this.props.name].filter(row => {
                    if(row[this.props.id] == id[0]){
                        return true;
                    }
                    return false;
                });
                var readonly = {};
                for(let key in this.props.readonly){
                    readonly[this.props.readonly[key]] = rows[0][key];
                }
                this.props.dispatch({type: 'SET_READONLY', readonly: readonly});
            }
            var modal = Object.assign({}, this.props.modals[evtKey]);
            modal.args = id;
            modal.tableName = this.props.name;
            modal.refreshAction = this.props.source;
            this.props.dispatch({type: 'OPEN_MODAL', template: modal});
        }else if("panels" in this.props && evtKey in this.props.panels){
            hashHistory.push('/subpanel/' + this.props.panels[evtKey] + '/' + this.props.panel.server + '/' + id[0]);
        }else{
            data = {"server_name": this.props.panel.server, "action": evtKey, "args": id};
            Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
                if(typeof msg === 'string'){
                    this.props.dispatch({type: 'SHOW_ALERT', msg});
                }else{
                    let { source, panel, name, refreshActions } = this.props;
                    data.action = source;
                    data.args = [];
                    if('args' in panel && panel.args !== ""){
                        data.args = [panel.args];
                    }
					if(refreshActions){
						data.call_functions = refreshActions;
					}
                    Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
						if(refreshActions){
                            this.props.dispatch({type: 'CHANGE_MULTI_DATA', data: msg});
						}else if(typeof msg !== 'string'){
                            this.props.dispatch({type: 'CHANGE_DATA', data: msg, name});
                        }else{
                            this.props.dispatch({type: 'SHOW_ALERT', msg});
                        }
                    });
                }
            }).fail(msg => {
                this.props.dispatch({type: 'SHOW_ALERT', msg});
            });
        }
    }
    linkClicked(action, event){
        var linkVal = event.currentTarget.textContent, args = "";
        if(window.location.hash.indexOf('subpanel') > -1){
            args = this.props.panel.args + ","; 
        }
        args += linkVal;
        if("panels" in this.props && action in this.props.panels){
            hashHistory.push('/panel/' + this.props.panels[action] + '/' + this.props.panel.server + '/' + args);
        }else if("subpanels" in this.props && action in this.props.subpanels){
            hashHistory.push('/subpanel/' + this.props.subpanels[action] + '/' + this.props.panel.server + '/' + args);
        } else {
             args = this.props.table.path.concat(linkVal);
             var data = {"server_name": this.props.panel.server, "action": action, "args": args};
             Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
                 if(typeof msg === 'string'){
                     this.props.dispatch({type: 'SHOW_ALERT', msg});
                 }else{
                     this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: this.props.name, passVal: linkVal});
                 }
             }).fail(msg => {
                 this.props.dispatch({type: 'SHOW_ALERT', msg});
             });
        }
    }
    render () {
        var pagination = true;
        if(typeof this.props.pagination !== 'undefined') pagination = this.props.pagination;
        if(typeof this.props.table[this.props.name] === 'undefined')
            return null;
        var cols = [], tbl_cols = this.props.columns.slice(0), tbl_id = this.props.id;
        for(var i=0; i<tbl_cols.length; i++){
            var tmp = Object.assign({}, tbl_cols[i]);
            if(tmp.key === ""){
                tmp.key = this.props.name;
                tmp.label = this.props.name;
            }
            var style = null;
            if("width" in tmp){
                style = {"width": tmp.width};
            }
            cols.push(tmp.key);
            tbl_cols[i] = (
                <Th key={tmp.key} column={tmp.key} style={style}>{tmp.label}</Th>
            );
        }
        if(!tbl_id){
            tbl_id = this.props.name;
        }
        var action_col = false, action_length = 0;
        if(this.props.hasOwnProperty('actions')){
            action_col = true; 
            action_length = this.props.actions.length;
            if(action_length > 1){
                var actions = this.props.actions.map(function(action) {
                    var className = "";
                    if(typeof action.class !== 'undefined'){
                        className = action.class;
                    }
                    return (
                        <Bootstrap.MenuItem key={action.name} eventKey={action.action} className={className}>{action.name}</Bootstrap.MenuItem>
                    );
                });
            }
        }
        var rows = this.props.table[this.props.name].map((row) => {
            var columns, key;
            if(typeof row === "string"){
                key = [this.props.name, row];
                columns = (
                    <Td key={cols[0]} column={cols[0]}>
                        {row}
                    </Td>
                );
            }else{
                if(tbl_id instanceof Array){
                    key = [];
                    for(var i=0; i<tbl_id.length; i++){
                        key.push(row[tbl_id[i]]);
                    }
                }else{
                    key = [row[tbl_id]];
                }
                columns = this.props.columns.map((col, index) => {
                    var key = col.key, colClass = "", colText = row[key], colVal = row[key];
                    if(typeof col.href !== 'undefined'){
                        colText = <a href={colVal} target='_blank'>Link</a>
                    }
                    else if(typeof col.colClass !== 'undefined'){
                        colClass = col.colClass;
                        if(row[col.colClass]){
                            colClass = "col-" + col.colClass + "-" + row[col.colClass];
                        }
                        colText = <span className={colClass}>{colVal}</span>;
                        if("action" in col){
                            var col_arr = col['action'].split(':');
                            if(col_arr[0] === "all" || col_arr[0] === row[col.colClass])
                                colText = <span className={colClass} onClick={this.linkClicked.bind(this, col_arr[1])}>{colVal}</span>
                        }
                    }
                    return (
                        <Td key={key} column={key} value={colVal}>
                            {colText}
                        </Td>
                    );
                });
            }
            if(action_col){
                action_col = (
                    <Td column="action">
                        {action_length > 1 ? (
                            <Bootstrap.DropdownButton id={"dropdown-" + key[0]} bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, key)}>
                                {actions}
                            </Bootstrap.DropdownButton>
                        ) : (
                            <Bootstrap.Button bsStyle='primary' onClick={this.btn_clicked.bind(this, key, this.props.actions[0].action)}>
                                {this.props.actions[0].name}
                            </Bootstrap.Button>
                        )}
                    </Td>
                );
            }
            var rowClass = "";
            if(typeof this.props.rowStyleCol !== 'undefined'){
                rowClass = "row-" + this.props.rowStyleCol + "-" + row[this.props.rowStyleCol];
            }
            return (
                <Tr className={rowClass} key={key}>
                    {columns}
                    {action_col}
                </Tr>
            )
        });
        var filterBy = "";
        if('filter' in this.props){
            filterBy = this.props.filter.filterBy;
        }
        var className = "table striped";
        if('class' in this.props){
            className += " " + this.props.class;
        }
        return (
            <div>
            { pagination ? ( <Reactable className={className} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={cols} >
                <Thead>
                    {tbl_cols}
                </Thead>
                {rows}
            </Reactable> ) :
            ( <Reactable className={className} filterable={cols} filterBy={filterBy} noDataText="No matching records found." sortable={true} hideFilterInput >
                <Thead>
                    {tbl_cols}
                </Thead>
                {rows}
            </Reactable> )}
            </div>
        );
    }
}

class Modal extends Component {

    constructor (props) {
        super(props);
        let content = this.props.modal.template.content, data = {};
        for(var j=0; j<content.length; j++){
            let modalElem = content[j];
            if(modalElem.type == "Form"){
                var elem = modalElem.elements;
                for(let i=0; i<elem.length; i++){
                    let { type, value, name } = elem[i];
                    if(type === 'dropdown')
                        data[name] = elem[i].values[0];
                    else if(type === 'checkbox')
                        data[name] = value || false;
                    else if(type !== 'label')
                        data[name] = value;
                }
            }
        }
        this.state = {
            data,
            focus: ""
        };
        this.close = this.close.bind(this);
        this.action = this.action.bind(this);
        this.form_changed = this.form_changed.bind(this);
    }

    close () {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }

    action (action_name) {
        let template = this.props.modal.template;
        let modalKwargs = template.kwargs || {};
        let kwargs = Object.assign(modalKwargs, this.state.data);
        let panel = this.props.panel;
        let data = { "server_name": panel.server, "action": action_name, kwargs };
        if("args" in template){
            data.args = template.args;
        }
        if('refreshActions' in template){
            data.call_functions = template.refreshActions;
        }
        Network.post("/api/panels/action", this.props.auth.token, data).done((d) => {
            this.props.dispatch({type: 'CLOSE_MODAL'});
            if('refreshAction' in template){
                let args = [];
                let { refreshAction, tableName } = template;
                if(panel.args !== "") args = [panel.args];
                var data = {"server_name": panel.server, "action": refreshAction, "args": args};
                Network.post('/api/panels/action', this.props.auth.token, data).done((msg) => {
                    if(typeof msg !== 'string'){
                        this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: tableName});
                    }else{
                        this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                    }
                });
            }
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    form_changed(e) {
        let { name, value, type } = e.target;
        var data = Object.assign({}, this.state.data);
        let state = {};
        if(type == "checkbox"){
            value = e.target.checked;
        }else{ //can't focus checkbox
            state.focus = name;
        }
        data[name] = value;
        state.data = data;
        this.setState(state);
    }

    render () {
        let redux = {}, action;
        let { template, isOpen } = this.props.modal;
        let btns = template.buttons.map((btn) => {
            if(btn.action == "cancel"){
                action = this.close;
            }else{
                action = this.action.bind(this, btn.action);
            }
            return { label: btn.name, onClick: action, bsStyle: btn.class };
        });

        var elements = template.content.map(element => {
            element.key = element.name;
            var Component = components[element.type];
            if(element.type == "Form"){
                element.data = this.state.data;
                element.form_changed = this.form_changed;
                element.focus = this.state.focus;
                element.modal = true;
            }
            redux[element.type] = getReduxComponent(Component, element.reducers);
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        });
        return (
            <Bootstrap.Modal show={isOpen} onHide={this.close}>
                { getModalHeader(template.title) }
                <Bootstrap.Modal.Body>
                    {elements}
                </Bootstrap.Modal.Body>
                { getModalFooter(btns) }
            </Bootstrap.Modal>
        );
    }
}

class Path extends Component {
	onClick(evt) {
		// console.log(evt.currentTarget.id)
		// console.log(evt.currentTarget.textContent);
		if(evt.currentTarget.id == 0) return;
		var args = this.props.table.path.slice(0, parseInt(evt.currentTarget.id) + 1);
		var data = {"server_name": this.props.panel.server, "action": this.props.action, "args": args};
		Network.post('/api/panels/action', this.props.auth.token, data).done((msg) => {
			if(typeof msg === 'string'){
				this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
			}else{
				this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: this.props.target, initVal: args});
			}
		}).fail((msg) => {
			this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
		});
	}
    render () {
        var paths = [];
        if("path" in this.props.table){
            //TODO remove link from first element in path
            //paths[0] = <li key="0" className="breadcrumb-item">{path}</li>;
            //var p = this.props.table.path.slice(1);
            paths =  this.props.table.path.map((path, i) => {
                return <li key={i} className="breadcrumb-item"><span id={i} className="link" onClick={(e) => this.onClick(e)}>{path}</span></li>;
            });
        }
        return (
            <ol className="breadcrumb">
                {paths}
            </ol>
        );
    }
}

class Form extends Component {

    onSelect (action) {
        var dropdown = findDOMNode(this.refs.dropdown);
        var host = dropdown.value.trim();
        var d_name = dropdown.name;
        var data = {"server_name": this.props.panel.server, "action": action, "args": [host]};
        Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
            if(typeof msg === 'string'){
                this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            }else if('val' in msg){
                this.props.dispatch({type: 'SELECT', select: host, name: d_name});
                this.props.dispatch({type: 'CHANGE_DATA', data: msg.list, name: this.props.target, initVal: [host, msg.val]});
            }else{
                this.props.dispatch({type: 'SELECT', select: host, name: d_name});
                this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: this.props.target, initVal: [host]});
            }
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }

    componentDidMount(){
        // TODO this code should be removed when modal is not rerendered on every keystroke
        if("focus" in this.props && this.props.focus){
            var elem = this.refs[this.props.focus], pos = elem.value.length;
            elem.focus();
            elem.setSelectionRange(pos, pos);
        }
    }

    render () {
        var redux = {};

        var inputs = this.props.elements.map((element, index) => {
            var { type, name } = element;
            if(type.charAt(0) === type.charAt(0).toLowerCase()){
                if(type == "checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={name} name={name} checked={this.props.data[name]} inline onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "label"){
                    return ( <label id={index} key={name} name={name} className="block">{element.value.split('\n').map(function(item, key){
                        return <span key={key}>{item}<br/></span>
                    })}</label>);
                }
                if(type == "multi_checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={name} name={name} checked={this.props.data[name]} onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "readonly_text"){
                    return ( <input id={index} key={name} className="form-control" type={type} name={name} value={this.props.form.readonly[name]} disabled /> );
                }
                if(type == "dropdown"){
                    var action = "", defaultValue = "", values = element.values;
                    if('modal' in this.props){
                        let selectInput = (<select id={index} key={name} name={name} defaultValue={this.props.data[name]} onChange={this.props.form_changed} ref={name}>
                                    {values.map(function(option, i) {
                                        return <option key={i} value={option}>{option}</option>
                                    })}
                                </select>);
                        if('label' in element)
                            return <div class="form-group">
                                <label for={index}>{element.label}</label>
                                {selectInput}
                            </div>;
                        else return selectInput;
                    }
                    else if('form' in this.props && name in this.props.form.dropdowns){
                        let d_elem = this.props.form.dropdowns[name];
                        defaultValue = d_elem.select;
                        values = d_elem.values;
                    }else{
                        defaultValue = element.value[0];
                        values = element.value;
                    }
                    if("action" in element){
                        action = this.onSelect.bind(this, element.action);
                    }
                    let selectInput = ( <select ref="dropdown" id={index} key={name} onChange={action} name={name} defaultValue={defaultValue}>
                        {values.map(function(option, i) {
                            return <option key={i} value={option}>{option}</option>
                        })}
                    </select> );
                    if('label' in element)
                        return <div class="form-group">
                                <label for={index}>{element.label}</label>
                                {selectInput}
                            </div>;
                    else return selectInput;
 
                }
                return ( <input id={index} key={name} type={type} name={name} className="form-control" value={this.props.data[name]} placeholder={element.label} onChange={this.props.form_changed} ref={name} /> );
            }
            element.key = name;
            //if(Object.keys(redux).indexOf(type) < 0){
            if(type == "Button" && element.action == "modal"){
                var modalTemplate = Object.assign({}, element.modal), args = [];
                if('panel' in this.props && 'args' in this.props.panel && this.props.panel.args){
                    args.push(this.props.panel.args);
                }
                if('args' in this.props){
                    for(var key in this.props.args){
                        let val = this.props.args[key]
                        if(!val){
                            val = this.props.name;
                        }
                        args.push(val);
                    }
                }
                modalTemplate.args = args;
                element.modalTemplate = modalTemplate;
            }
            var Component = components[type];
            redux[type] = getReduxComponent(Component, element.reducers);
            var Redux = redux[type];
            return React.createElement(Redux, element);
        });

        return (
            <form className={this.props.class}>
                {inputs}
            </form>
        );
    }
}

class FilterForm extends Component {
    constructor(props) {
        super(props);
        let inputs = {}, selects = [];
        this.props.elements.map(elem => {
            let { name, type, value } = elem;
            if(type !== 'date' && type !== 'dates'){
                inputs[name] = value;
                if(type === 'multiSelect'){
                    selects.push(name);
                }
            }
        });
        this.state = {
            ...inputs,
            startDate: null,
            endDate: null,
			date: null,
            focusedInput: null,
            focused: false,
            selects,
            isOpen: false
        };
        this.sendFilter = this.sendFilter.bind(this);
        this.open = this.open.bind(this);
        this.close = this.close.bind(this);
    }
    sendFilter(){
        const {startDate, endDate, selects} = this.state;
        let data = Object.assign({}, this.state);
        if(startDate && endDate){
            data.date_from = startDate.unix();
            data.date_to = endDate.unix();
        }
        if(selects.length > 0){
            selects.map(name => {
                data[name] = data[name].map(elem => elem.value);
            });
        }
        //['startDate', 'endDate', 'date', 'focusedInput', 'focused', 'selects'].forEach(key => delete data[key]);
        data = {"server_name": this.props.panel.server, "action": this.props.action, "kwargs": data};
        Network.post('/api/panels/action', this.props.auth.token, data).done(msg => {
            this.props.dispatch({type: 'CHANGE_DATA', name: this.props.target, data: msg});
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }
    open(){
        this.setState({isOpen: true});
    }
    close(){
        this.setState({isOpen: false});
    }
    render(){
        let inputs = this.props.elements.map(elem => {
            let { name, type, label } = elem, input;
            switch(type){
                case 'dates':
                    input = (
						<DateRangePicker
							displayFormat="DD/MM/YYYY"
							startDate={this.state.startDate}
							endDate={this.state.endDate}
							onDatesChange={({ startDate, endDate }) => this.setState({ startDate, endDate })}
							focusedInput={this.state.focusedInput}
							onFocusChange={focusedInput => this.setState({ focusedInput })}
							isOutsideRange={() => false}
						/>
                    );
                    break;
                case 'date':
                    input = (
						<SingleDatePicker 
							displayFormat="DD/MM/YYYY"
							date={this.state.date}
                            focused={this.state.focused}
							onDateChange={date => this.setState({date})}
                            onFocusChange={focused => this.setState({ focused })}
						/>
                    );
                    break;
                case 'multiSelect':
                    input = <Select options={elem.values} multi={true} placeholder={label} value={this.state[name]} onChange={val => this.setState({[name]: val})} />;
                    break;
                default:
                    input = <input type={type} className="form-control" value={this.state[name]} onChange={e => this.setState({[name]: e.target.value})} />;
                    break;
            }
            return (
                <div className="form-group">
                    <label>{name}</label>
                    {input}
                </div>
            );
        });
        return (
            <div>
                <button className='btn btn-default' onClick={this.open}>Filter</button>
                <Bootstrap.Modal show={this.state.isOpen} onHide={this.close}>
                    { getModalHeader(this.props.title) }
                    <Bootstrap.Modal.Body>
                        <form>
                            {inputs}
                        </form>
                    </Bootstrap.Modal.Body>
                    { getModalFooter([{label: 'Filter', bsStyle: 'primary', onClick: this.sendFilter}]) }
                </Bootstrap.Modal>
            </div>
        );
    }
}

class CustomChart extends Component {
    constructor(props) {
        super(props);
        let chartData = {chartData: this.parseData(props)};
        this.state = chartData;
    }
    parseData(props) {
        let { table, target, xCol, xColType, datasets, column, chartType } = props, xData = [];
        let data = Object.assign([], datasets), chartData = {};
        if(xCol){
            if(xColType == 'date'){
                table[target].map((row) => {
                    xData.push(new Date(row[xCol] * 1000));
                    data.forEach(elem => {
                        elem.data.push(row[elem.column]);
                    });
                });
            }
            if(chartType == 'pie'){
				data.forEach(elem => {
					elem.backgroundColor = [];
					elem.hoverBackgroundColor = [];
				});
				table[target].map((row) => {
					xData.push(row[xCol]);
					data.forEach(elem => {
						elem.data.push(row[elem.column]);
                        let color = getRandomColor();
                        elem.backgroundColor.push(color);
                        elem.hoverBackgroundColor.push(color);
					});
				});
            }else {
				table[target].map((row) => {
					xData.push(row[xCol]);
					data.forEach(elem => {
						elem.data.push(row[elem.column]);
					});
				});
            }
        }else{
            //data.forEach(elem => {
            //    xData.push(elem.name);
            //});
			/*table[target].map((row) => {
                xData.push(row[xCol]);
                data.forEach(elem => {
                    elem.data.push(row[column]);
                });
			});*/
		}
        chartData.labels = xData;
        chartData.datasets = data;
        return chartData;
    }
    componentWillReceiveProps(nextProps) {
        let chartData = this.parseData(nextProps);
        this.setState({ chartData });
    }
    render() {
        let { name, height, width, chartType, xColType, options } = this.props, chart;
        //let co = xColType == 'date' ? chartOptionsTime : chartOptions;
        switch(chartType) {
            case 'line':
                chart = <Line height={height || 200} width={width || 200} data={this.state.chartData} options={options} redraw />;
                break;
            case 'pie':
                chart = <Pie height={height || 200} width={width || 200} data={this.state.chartData} options={options}/>;
                break;
            case 'bar':
                chart = <Bar height={height || 200} width={width || 200} data={this.state.chartData} options={options} redraw />
                break;
        }
        return (
            <div>
                {chart}
            </div>
        );
    }
}

components.Div = Div;
components.MultiTable = MultiTable;
components.Chart = Chart;
components.Table = Table;
components.Form = Form;
components.Modal = Modal;
components.Path = Path;
components.CustomChart = CustomChart;
components.FilterForm = FilterForm;

module.exports = components;
