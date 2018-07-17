import React, { Component } from 'react';
import { Table, Tr, Td } from 'reactable';
import { Button, DropdownButton, MenuItem, Modal, FormGroup } from 'react-bootstrap';
import { connect } from 'react-redux';
var Network = require('../network');

function isEmpty(obj) {
    for(var key in obj) {
        if(obj.hasOwnProperty(key))
            return false;
    }
    return true;
}

var stringToColour = function(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    var colour = '#';
    for (var i = 0; i < 3; i++) {
      var value = (hash >> (i * 8)) & 0xFF;
        colour += ('00' + value.toString(16)).substr(-2);
    }
    return colour;
}
// stringToColour("greenish");
// -> #9bc63b

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}
function getRandomColors(count) {
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
}
function arr2str(arr, delimiter=', ') {
    return arr.join(delimiter);
}
function str2arr(str, delimiter=', ') {
    return str.split(delimiter);
}
function obj2str(obj, key){
    return obj[key];
}
function reduceArr(arr, key){
    return arr.map(obj => obj[key]);
}
function objArr2str(arr, key) {
    return arr2str(reduceArr(arr, key));
}
function getTableRow(columns, data) {
    return columns.map((col, index) => {
        return <Td key={col} column={col}>{data[index]}</Td>;
    });
}
function getTableRowWithLink(columns, data, onClick, index) {
    let result = [<Td key={columns[0]} column={columns[0]}><span className="link" onClick={onClick.bind(null, data[0], index)}>{data[0]}</span></Td>];
    return result.concat(getTableRow(columns.slice(1), data.slice(1)));
}
function getTableRowWithAction(columns, data, btnText, btnVal, btnClick, onLinkClick, rowIndex) {
    let rows = onLinkClick ? getTableRowWithLink(columns, data, onLinkClick, rowIndex) : getTableRow(columns, data);
    rows.push(<Td key="Actions" column="Actions"><Button type="button" bsStyle='primary' onClick={btnClick} value={btnVal}>{btnText}</Button></Td>);
    return rows;
}
function getTableRowWithActions(columns, data, actions, action, param, onLinkClick, rowIndex) {
    let rows = onLinkClick ? getTableRowWithLink(columns, data, onLinkClick, rowIndex) : getTableRow(columns, data);
    let items = actions.map(a => {
        return <MenuItem key={a} eventKey={a}>{a}</MenuItem>
    });
    rows.push((
        <Td key="Actions" column="Actions">
            <DropdownButton bsStyle='primary' title="Choose" onSelect={action.bind(null, param, rowIndex)}>{items}</DropdownButton>
        </Td>
        ));
    return rows;
}
function getModalHeader(title){
    return (
        <Modal.Header closeButton>
            <Modal.Title>{title}</Modal.Title>
        </Modal.Header>
    );
}
function getModalFooter(buttons){
    let btns = buttons.map((btn, i) => {
        let { label, bsStyle, onClick } = btn;
        return <Button key={i} onClick={onClick} bsStyle={bsStyle}>{label}</Button>;
    });
    return (
        <Modal.Footer>
            { btns }
        </Modal.Footer>
    );
}

function initializeFields(fields) {
    let state = {};
    for(let i=0; i<fields.length; i++)
        state[fields[i].key] = "";
    return state;
}

function initializeFieldsWithValues(fields, values) {
    let state = {}
    for(let i=0; i<fields.length; i++){
        let key = fields[i].key;
        state[key] = values[key];
    }
    return state;
}

function initSelectOptions(arr){
    return arr.map(o => ({label: o, value: o}));
}

function getReduxComponent(ReactComponent, reducers){
    return connect(state => {
        let newstate = {auth: state.auth};
        if(reducers){
            for (let i = 0; i < reducers.length; i++) {
                let r = reducers[i];
                newstate[r] = state[r];
            }
        }
        return newstate;
    })(ReactComponent);
}

function callPanelAction(token, data, callbackSuccess, callbackError){
    Network.post('/api/panels/action', token, data).done(msg => {
        if(typeof msg === 'string'){
            callbackSuccess(msg);
        }
    }).fail(msg => {
        callbackError(msg);
    });
}

function download(url, token, data, fileWithExt, callback){
    Network.download_file(url, token, data).done(function(d) {
        var data = new Blob([d], {type: 'octet/stream'});
        var url = window.URL.createObjectURL(data);
        let tempLink = document.createElement('a');
        tempLink.style = "display: none";
        tempLink.href = url;
        tempLink.setAttribute('download', fileWithExt);
        document.body.appendChild(tempLink);
        tempLink.click();
        setTimeout(function(){
            document.body.removeChild(tempLink);
            window.URL.revokeObjectURL(url);
        }, 100);
    }).fail(function (msg) {
        callback(msg);
    });
}

function getSpinner(style){
    return <div className="spinner" style={style}></div>;
}

function capitalizeFirstLetter(text){
    return text[0].toUpperCase() + text.substr(1);
}

function getFormFields(fields){
    return fields.map(f => {
        return (
            <FormGroup>
                <label className={`col-sm-${12-f.size} control-label`}>{f.label}</label>
                <div className={`col-sm-${f.size}`}>
                    <input type={f.type} className="form-control" ref={f.key} />
                </div>
            </FormGroup>
        );
    });
}

function findObjInArr(arr, param, term){
    for(var i = 0; i < arr.length; i++){
        if(arr[i][param] === term)
            return arr[i];
    }
    return null;
}

function getTimestamp(dateObj, seconds){
    return new Date(dateObj.getTime() - 1000*seconds).getTime();
}

module.exports = {
    isEmpty,
    stringToColour,
    getRandomColor,
    getRandomColors,
    getTableRow,
    getTableRowWithAction,
    getTableRowWithActions,
    getModalHeader,
    getModalFooter,
    initializeFields,
    initializeFieldsWithValues,
    arr2str,
    reduceArr,
    objArr2str,
    initSelectOptions,
    getReduxComponent,
    callPanelAction,
    download,
    getSpinner,
    capitalizeFirstLetter,
    getFormFields,
    findObjInArr,
    getTimestamp
}
