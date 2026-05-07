# -*- coding: utf-8 -*-
"""
Validation Metrics Module
Calculates advanced metrics for ML model validation
"""

import numpy as np
from sklearn.metrics import (
    cohen_kappa_score, f1_score, matthews_corrcoef, 
    confusion_matrix, recall_score, precision_score
)
from collections import defaultdict


class ValidationMetrics:
    """Calculate validation metrics for classification models"""

    @staticmethod
    def calculate_kappa(y_true, y_pred):
        """
        Calculate Cohen's Kappa coefficient
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            float: Kappa coefficient (-1 to 1)
        """
        return cohen_kappa_score(y_true, y_pred)

    @staticmethod
    def calculate_qadi(y_true, y_pred):
        """
        Calculate QADI (Quantity and Allocation Disagreement Index)
        
        QADI = sqrt((A/N)^2 + (Q/N)^2)
        where:
            A = number of incorrectly labeled pixels
            Q = difference in pixel count per class
            N = total number of pixels
            
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            float: QADI index (0 to 1, lower is better)
        """
        N = len(y_true)
        
        # Count allocation disagreement (A)
        A = np.sum(y_true != y_pred)
        
        # Count quantity disagreement (Q)
        classes = np.unique(np.concatenate([y_true, y_pred]))
        Q = 0
        for cls in classes:
            count_true = np.sum(y_true == cls)
            count_pred = np.sum(y_pred == cls)
            Q += abs(count_true - count_pred)
        Q = Q / 2  # Divide by 2 because we count each difference twice
        
        # Calculate QADI
        qadi = np.sqrt((A / N) ** 2 + (Q / N) ** 2)
        return qadi

    @staticmethod
    def calculate_overall_accuracy(y_true, y_pred):
        """
        Calculate Overall Accuracy (OA)
        
        OA = (TP + TN) / (TP + TN + FP + FN)
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            float: Overall accuracy (0 to 1)
        """
        return np.sum(y_true == y_pred) / len(y_true)

    @staticmethod
    def calculate_f1_scores(y_true, y_pred):
        """
        Calculate F1-Score for each class
        
        F1 = 2 * (Precision * Recall) / (Precision + Recall)
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            dict: F1-scores per class
        """
        classes = np.unique(np.concatenate([y_true, y_pred]))
        f1_scores = {}
        
        for cls in classes:
            y_true_binary = (y_true == cls).astype(int)
            y_pred_binary = (y_pred == cls).astype(int)
            f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
            f1_scores[int(cls)] = f1
        
        return f1_scores

    @staticmethod
    def calculate_mcc(y_true, y_pred):
        """
        Calculate Matthews Correlation Coefficient (MCC)
        
        For multiclass: average of binary MCCs
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            float: MCC (-1 to 1)
        """
        classes = np.unique(np.concatenate([y_true, y_pred]))
        mcc_scores = []
        
        for cls in classes:
            y_true_binary = (y_true == cls).astype(int)
            y_pred_binary = (y_pred == cls).astype(int)
            mcc = matthews_corrcoef(y_true_binary, y_pred_binary)
            mcc_scores.append(mcc)
        
        return np.mean(mcc_scores)

    @staticmethod
    def calculate_producer_accuracy(y_true, y_pred):
        """
        Calculate Producer's Accuracy (Recall) per class
        
        PA = TP / (TP + FN)
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            dict: Producer's accuracy per class
        """
        classes = np.unique(np.concatenate([y_true, y_pred]))
        producer_acc = {}
        
        for cls in classes:
            y_true_binary = (y_true == cls).astype(int)
            y_pred_binary = (y_pred == cls).astype(int)
            recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
            producer_acc[int(cls)] = recall
        
        return producer_acc

    @staticmethod
    def calculate_user_accuracy(y_true, y_pred):
        """
        Calculate User's Accuracy (Precision) per class
        
        UA = TP / (TP + FP)
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            dict: User's accuracy per class
        """
        classes = np.unique(np.concatenate([y_true, y_pred]))
        user_acc = {}
        
        for cls in classes:
            y_true_binary = (y_true == cls).astype(int)
            y_pred_binary = (y_pred == cls).astype(int)
            precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
            user_acc[int(cls)] = precision
        
        return user_acc

    @staticmethod
    def calculate_all_metrics(y_true, y_pred):
        """
        Calculate all metrics at once
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            dict: All calculated metrics
        """
        metrics = ValidationMetrics()
        
        return {
            'overall_accuracy': metrics.calculate_overall_accuracy(y_true, y_pred),
            'kappa': metrics.calculate_kappa(y_true, y_pred),
            'qadi': metrics.calculate_qadi(y_true, y_pred),
            'mcc': metrics.calculate_mcc(y_true, y_pred),
            'f1_scores': metrics.calculate_f1_scores(y_true, y_pred),
            'producer_accuracy': metrics.calculate_producer_accuracy(y_true, y_pred),
            'user_accuracy': metrics.calculate_user_accuracy(y_true, y_pred),
        }
