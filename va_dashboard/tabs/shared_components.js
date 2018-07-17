import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');

const ConfirmPopup = (props) => {
    return (
        <Bootstrap.Modal show={props.show} onHide={props.close}>
            <Bootstrap.Modal.Header closeButton>
                <Bootstrap.Modal.Title>Confirm action</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <p>{props.body}</p>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
                <Bootstrap.Button onClick={props.close}>Cancel</Bootstrap.Button>
                <Bootstrap.Button onClick={props.action.bind(null, ...props.data)} bsStyle = "primary">Confirm</Bootstrap.Button>
            </Bootstrap.Modal.Footer>
        </Bootstrap.Modal>
    );
}

const TextPopup = (props) => {
    let { show, body, title } = props.data;
    return (
        <Bootstrap.Modal show={show} onHide={props.close}>
            <Bootstrap.Modal.Header closeButton>
                <Bootstrap.Modal.Title>{title}</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body bsClass='modal-body scrollable'>
                <p dangerouslySetInnerHTML={{__html: body}}></p>
            </Bootstrap.Modal.Body>

        </Bootstrap.Modal>
    );
}

class PivotTable extends Component{
    constructor(props){
        super(props);
        let inList = [], notInList = [], rows = {};
        this.props.data.forEach(elem => {
            if(elem.key in this.props.dataSource[0]){
                inList.push(elem);
            }else{
                notInList.push(elem);
            }
        });
        this.props.dataSource.forEach(elem => {
            let result = {};
            inList.forEach(e => {
                result[e.key] = elem[e.key];
            });
            notInList.forEach(e => {
                result[e.key] = this.sumRows(e.type, e.key, elem.subRows);
            });
            rows[elem[this.props.rows[0].key]] = result;
        });
        this.state = {
            selected: [],
            rows
        };
        this.getTableData = this.getTableData.bind(this);
        this.selectRow = this.selectRow.bind(this);
    }

    getTableData(source, row, result){
        source.forEach(elem => {
            result.push(<td>{row[elem.key]}</td>);
        });
        return result;
    }

    selectRow(key){
        let selected = Object.assign([], this.state.selected);
        let index = selected.indexOf(key);
        if(index > -1){
            selected.splice(index, 1);
        }else{
            selected.push(key);
        }
        this.setState({selected});
    }

    sumRows(type, key, data){
        let result = '', obj = {};
        switch(type){
            case 'number':
                result = 0;
                data.forEach(d => {
                    result += d[key] ? d[key] : 0;
                });
                break;
            case 'string':
                data.forEach(d => {
                    if(d[key])
                        obj[d[key]] = '';
                });
                result = Object.keys(obj).join(', ');
                break;
            case 'count':
                data.forEach(d => {
                    let elem = d[key];
                    if(elem)
                        obj[elem] = elem in obj ? ++obj[elem] : 1;
                });
                for(let key in obj){
                    result += `${obj[key]} ${key}, `;
                }
                result = result.slice(0, -2);
                break; 
        }
        return result;
    }

    render(){
        let ths = this.props.data.map(elem => <th>{elem.label}</th>);
        let selected = this.state.selected;
        return ( 
        <div className="pivot-table">
            <table className="table">
                <thead>
                    <tr>{[<th></th>, <th></th>].concat(ths)}</tr>
                </thead>
                <tbody>
                    {this.props.dataSource.map(row => {
                        let tblKey = this.props.rows[0].key;
                        if(selected.indexOf(row[tblKey]) > -1){
                            let tblKey2 = this.props.rows[1].key;
                            let trs = [], tds = [];
                            if(row.subRows.length > 0){
                                let firstRow = row.subRows[0];
                                tds.push(<td><span className='glyphicon glyphicon-chevron-down' onClick={this.selectRow.bind(null, row[tblKey])}></span>{row[tblKey]}</td>);
                                tds.push(<td>{firstRow[tblKey2]}</td>);
                                tds = this.getTableData(this.props.data, firstRow, tds);
                                trs.push(<tr key={firstRow[tblKey2]}>{tds}</tr>);
                                row.subRows.slice(1).forEach(subRow => {
                                    tds = [<td></td>, <td>{subRow[tblKey2]}</td>];
                                    tds = this.getTableData(this.props.data, subRow, tds);
                                    trs.push(<tr key={subRow[tblKey2]}>{tds}</tr>);
                                });
                                tds = [<th colSpan="2">Sum</th>];
                                tds = this.getTableData(this.props.data, this.state.rows[row[tblKey]], tds);
                                trs.push(<tr key="sum" className="sumRow">{tds}</tr>);
                            }
                            return trs;
                        }else {
                            let tds = [<td colSpan="2"><span className='glyphicon glyphicon-chevron-right' onClick={this.selectRow.bind(null, row[tblKey])}></span>{row[tblKey]}</td>];
                            tds = this.getTableData(this.props.data, this.state.rows[row[tblKey]], tds);
                            return (
                                <tr key={row[tblKey]}>{tds}</tr>
                            )
                        }
                    })}
                </tbody>
            </table> 
        </div> 
        );
    }
}

module.exports = {
    ConfirmPopup,
    PivotTable,
    TextPopup
};
