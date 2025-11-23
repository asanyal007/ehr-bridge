import React from 'react';
import { components, colors } from '../../designSystem';
import Card, { CardBody, CardFooter, CardHeader } from '../Common/Card';
import Badge from '../Common/Badge';
import Button from '../Common/Button';

const JobCard = ({ job, onSelect, onDelete, isSelected }) => {
    const statusVariant = {
        DRAFT: 'info',
        ANALYZING: 'warning',
        PENDING_REVIEW: 'warning',
        APPROVED: 'success',
        ERROR: 'error',
        COMPLETED: 'success',
        RUNNING: 'info',
        STOPPED: 'neutral',
        PAUSED: 'warning'
    }[job.status] || 'info';

    return (
        <Card
            className={`group hover:border-primary-200 transition-all duration-200 ${isSelected ? 'ring-2 ring-primary-500 border-transparent' : ''}`}
        >
            <CardHeader>
                <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full bg-${statusVariant}-500`} />
                    <h3 className="text-lg font-semibold text-gray-900 truncate" title={job.jobId}>
                        {job.name || `Job ${job.jobId.substring(0, 8)}`}
                    </h3>
                </div>
                <Badge variant={statusVariant}>{job.status}</Badge>
            </CardHeader>

            <CardBody>
                <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Source</span>
                        <span className="font-medium text-gray-900 truncate max-w-[150px]">{job.sourceType || 'CSV'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Target</span>
                        <span className="font-medium text-gray-900 truncate max-w-[150px]">{job.targetType || 'FHIR'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Created</span>
                        <span className="font-medium text-gray-900">
                            {new Date(job.createdAt).toLocaleDateString()}
                        </span>
                    </div>
                </div>
            </CardBody>

            <CardFooter className="flex justify-between items-center bg-gray-50/50">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete(job.jobId);
                    }}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                    Delete
                </Button>
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onSelect(job)}
                >
                    View Details
                </Button>
            </CardFooter>
        </Card>
    );
};

export default JobCard;
