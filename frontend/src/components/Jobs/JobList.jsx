import React from 'react';
import JobCard from './JobCard';
import Button from '../Common/Button';
import { animations } from '../../designSystem';

const JobList = ({ jobs, onSelectJob, onDeleteJob, onCreateJob, loading }) => {
    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="bg-white rounded-xl h-64 animate-pulse border border-gray-100" />
                ))}
            </div>
        );
    }

    if (jobs.length === 0) {
        return (
            <div className={`text-center py-20 bg-white rounded-xl border border-dashed border-gray-300 ${animations.fadeIn}`}>
                <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <span className="text-2xl">📭</span>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
                <p className="text-gray-500 mb-6">Get started by creating your first mapping job.</p>
                <Button onClick={onCreateJob}>Create New Job</Button>
            </div>
        );
    }

    return (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${animations.fadeIn}`}>
            {jobs.map((job) => (
                <JobCard
                    key={job.jobId}
                    job={job}
                    onSelect={onSelectJob}
                    onDelete={onDeleteJob}
                />
            ))}
        </div>
    );
};

export default JobList;
