# -*- coding: utf-8 -*-
"""
Confusion Matrix Module
Generate and manage confusion matrices
"""

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix as sklearn_confusion_matrix


class ConfusionMatrix:
    """Generate and manage confusion matrices"""

    @staticmethod
    def create_matrix(y_true, y_pred):
        """
        Create a confusion matrix
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            pd.DataFrame: Confusion matrix with class labels
        """
        classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
        cm = sklearn_confusion_matrix(y_true, y_pred, labels=classes)
        
        # Convert to DataFrame for better handling
        cm_df = pd.DataFrame(cm, index=classes, columns=classes)
        cm_df.index.name = 'Reference'
        cm_df.columns.name = 'Classified'
        
        return cm_df

    @staticmethod
    def create_normalized_matrix(y_true, y_pred, normalize='true'):
        """
        Create a normalized confusion matrix
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            normalize: 'true' (by reference), 'pred' (by prediction), or None
            
        Returns:
            pd.DataFrame: Normalized confusion matrix
        """
        classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
        cm = sklearn_confusion_matrix(y_true, y_pred, labels=classes)
        
        if normalize == 'true':
            # Normalize by reference (rows)
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        elif normalize == 'pred':
            # Normalize by prediction (columns)
            cm = cm.astype('float') / cm.sum(axis=0)[np.newaxis, :]
        
        cm_df = pd.DataFrame(cm, index=classes, columns=classes)
        cm_df.index.name = 'Reference'
        cm_df.columns.name = 'Classified'
        
        return cm_df

    @staticmethod
    def get_accuracy_metrics(cm_df):
        """
        Extract accuracy metrics from confusion matrix
        
        Args:
            cm_df: Confusion matrix DataFrame
            
        Returns:
            dict: Accuracy metrics per class
        """
        metrics = {}
        
        for cls in cm_df.index:
            # True Positives
            tp = cm_df.loc[cls, cls]
            
            # False Positives (sum of column except diagonal)
            fp = cm_df[cls].sum() - tp
            
            # False Negatives (sum of row except diagonal)
            fn = cm_df.loc[cls].sum() - tp
            
            # True Negatives (sum of all except row and column)
            tn = cm_df.values.sum() - cm_df.loc[cls].sum() - fp
            
            # Producer's Accuracy (Recall)
            producer_acc = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # User's Accuracy (Precision)
            user_acc = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            # F1-Score
            f1 = 2 * (user_acc * producer_acc) / (user_acc + producer_acc) if (user_acc + producer_acc) > 0 else 0
            
            metrics[int(cls)] = {
                'tp': int(tp),
                'fp': int(fp),
                'fn': int(fn),
                'tn': int(tn),
                'producer_accuracy': producer_acc,
                'user_accuracy': user_acc,
                'f1_score': f1
            }
        
        return metrics

    @staticmethod
    def get_overall_accuracy(cm_df):
        """
        Calculate overall accuracy from confusion matrix
        
        Args:
            cm_df: Confusion matrix DataFrame
            
        Returns:
            float: Overall accuracy
        """
        correct = np.trace(cm_df.values)
        total = cm_df.values.sum()
        return correct / total if total > 0 else 0

    @staticmethod
    def get_kappa_from_matrix(cm_df):
        """
        Calculate Cohen's Kappa from confusion matrix
        
        Args:
            cm_df: Confusion matrix DataFrame
            
        Returns:
            float: Kappa coefficient
        """
        n = cm_df.values.sum()
        po = np.trace(cm_df.values) / n  # Observed agreement
        
        # Expected agreement
        pe = 0
        for i in cm_df.index:
            pe += (cm_df.loc[i].sum() * cm_df[i].sum()) / (n * n)
        
        kappa = (po - pe) / (1 - pe) if pe < 1 else 0
        return kappa

    @staticmethod
    def format_matrix_for_display(cm_df, normalize=False):
        """
        Format confusion matrix for display
        
        Args:
            cm_df: Confusion matrix DataFrame
            normalize: Whether to normalize values
            
        Returns:
            str: Formatted matrix string
        """
        output = "\nConfusion Matrix:\n"
        output += "=" * 60 + "\n"
        
        if normalize:
            cm_display = cm_df.astype('float') / cm_df.sum(axis=1)[:, np.newaxis]
            output += cm_display.to_string(float_format=lambda x: f'{x:.4f}')
        else:
            output += cm_df.to_string()
        
        output += "\n" + "=" * 60 + "\n"
        
        # Add metrics
        metrics = ConfusionMatrix.get_accuracy_metrics(cm_df)
        output += "\nPer-Class Metrics:\n"
        output += "-" * 60 + "\n"
        
        for cls, metric in metrics.items():
            output += f"\nClass {cls}:\n"
            output += f"  TP: {metric['tp']}, FP: {metric['fp']}, "
            output += f"FN: {metric['fn']}, TN: {metric['tn']}\n"
            output += f"  Producer's Accuracy (Recall): {metric['producer_accuracy']:.4f}\n"
            output += f"  User's Accuracy (Precision): {metric['user_accuracy']:.4f}\n"
            output += f"  F1-Score: {metric['f1_score']:.4f}\n"
        
        return output
