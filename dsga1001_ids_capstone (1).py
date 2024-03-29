# -*- coding: utf-8 -*-
"""DSGA1001_IDS Capstone.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kTw9WIuBXTcjdMrOmra0yHMl1j-yBGuL

# Part I. Data Preprocess
"""

# Commented out IPython magic to ensure Python compatibility.
#import packages
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, Lasso, Ridge, LassoCV, RidgeCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from sklearn.neighbors import KernelDensity, NearestNeighbors
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.pipeline import Pipeline
from sklearn.metrics import silhouette_samples, silhouette_score
from statsmodels.stats.power import TTestIndPower
sns.set()
# %matplotlib inline

#import csv file to colab
#reference site: https://pythonviz.com/colab-jupyter/google-colab-notebook-file-io-csv-input-output/
from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/Data/Medicalpremium.csv')

df.info()

df.describe()

#Test for Normality
# Perform Shapiro-Wilk Test.
from scipy.stats import shapiro 
for col in df:
    print(col)
    s,p = shapiro(df.loc[:col])
    print(s,round(p,4))
    print()

df.corr(method='spearman')
#df.corr(method='pearson')

import seaborn as sns
sns.heatmap(df.corr(method='pearson'))

sns.heatmap(df.corr(method='spearman'))

# Compute Spearmann Correlation Coefficient (r) for each pair of variables
# Compute Pearson Correlation Coefficient (r) for each pair of variables
for col1 in df:
    corr_df = pd.DataFrame(columns = ['r', 'p'])
    for col2 in df:
        r , p = stats.spearmanr(df[col1], df[col2])
        #r , p = stats.pearsonr(df[col1], df[col2])
        corr_df.loc[col2] = [round(r,4),round(p,4)]
    print()
    print(col1)
    print(corr_df)

from sklearn.metrics import mean_absolute_error,r2_score, mean_squared_error
import random
scale = StandardScaler()
scaled = pd.DataFrame(scale.fit_transform(df))

random = random.seed(15020304) #N-number: 

x_train, x_test, y_train, y_test = train_test_split(scaled.iloc[:,:-1], scaled.iloc[:,-1], train_size=0.8,random_state=random)
print(x_train.shape, y_train.shape)

# LassoCV
lasso = LassoCV()
lasso.fit(x_train, y_train)
print(f'Optimal alpha: {lasso.alpha_}')

coef = dict()
for i in range(10):
  coef[df.columns[i]] = lasso.coef_[i]
print(f'coefficeints:\n{coef}')

y_pred = lasso.predict(x_test)
print(f'R^2: {lasso.score(x_test, y_test)}')
r2_lasso= lasso.score(x_test, y_test)
rmse_lasso = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'RMSE: {rmse_lasso}')

"""# Part II. Inference 

---

The motivation is to identify whether the premium price varies depending on certain variables. For example, I want to find if the premium price differs for customers with diabetes and customers without diabetes. To do so, I split the distribution into people with diabetes and people without diabetes, and use Welche's t-test to calculate the p-value. Using the alpha level of .05, I assess whether to reject or fail to reject the null hypothesis, which assumes that there is no difference in the distribution of the two group.


"""

def effect_size(df1, df2):
    std = np.sqrt(((df1.count() - 1)*df1.std()**2 + (df2.count() - 1)*df2.std()**2 )/(df1.count() + df2.count()))
    return (df1.mean() - df2.mean())/std

alpha=.05
power=.8

# Standardized premium price column
df['PremiumPrice']=(df['PremiumPrice']-df['PremiumPrice'].mean())/df['PremiumPrice'].std()

# Divide the distribution into two category. I divided into: 
# - people with diabetes or without diabetes,
# - people with ages above 50 and ages under 50, 
# - people with and without chronic disease, 
# - people who had no surgery and people with surgeries more than or equal to 1. 

diabetes_1 = df[(df['Diabetes'] == 1)]['PremiumPrice']
diabetes_0 = df[(df['Diabetes'] == 0)]['PremiumPrice']

age_above50 = df[df['Age'] >= 50]['PremiumPrice']
age_below50 = df[df['Age'] < 50]['PremiumPrice']

chronicDisease_1 = df[df['AnyChronicDiseases'] == 1]['PremiumPrice']
chronicDisease_0 = df[df['AnyChronicDiseases'] == 0]['PremiumPrice']

had_surgeries = df[df['NumberOfMajorSurgeries'] > 0]['PremiumPrice']
no_surgery = df[df['NumberOfMajorSurgeries'] == 0]['PremiumPrice']

"""Surgery distribution"""

# Power Analysis
effect_size_surgery = effect_size(had_surgeries, no_surgery)

# Perform power analysis to find sample size for given effect
obj = TTestIndPower()
n = obj.solve_power(effect_size=effect_size_surgery, alpha=alpha, power=power, 
                    ratio=1, alternative='two-sided')
  
print('Sample size/Number needed in each group: {:.3f}'.format(n))

had_surgeries.count(), no_surgery.count()

plt.subplots(1, 1, figsize=(10,6))
        
plt.hist(had_surgeries.values, alpha=.65, label='had more than one surgery', density=True)
plt.hist(no_surgery.values, alpha=.5, label='had no surgery', density=True)

mean1 = had_surgeries.values.mean()
mean0 = no_surgery.values.mean()

plt.vlines(mean1, 0, 1, color='navy', ls='--', label='Mean premium price for surgery > 0')
plt.vlines(mean0, 0, 1, color='red', ls='--', label='Mean premium price for no surgery')

ci_no_surgery = stats.t.interval(1 - alpha, len(no_surgery) - 1, loc=np.mean(no_surgery), scale=stats.sem(no_surgery))
ci_surgery = stats.t.interval(1 - alpha, len(had_surgeries) - 1, loc=np.mean(had_surgeries), scale=stats.sem(had_surgeries))

plt.vlines(ci_no_surgery[0], 0, 1, color='yellow', ls='--', label='Confidence Interval 95%')
plt.vlines(ci_no_surgery[1], 0, 1, color='yellow', ls='--')

plt.vlines(ci_surgery[0], 0, 1, color='yellow', ls='--')
plt.vlines(ci_surgery[1], 0, 1, color='yellow', ls='--')

plt.xlabel('Premium price')
plt.ylabel('Density')
plt.title('Premium price distribution based on surgery history')
plt.legend()

statistics, pval = stats.ttest_ind(no_surgery, had_surgeries, equal_var=False)
print("The p-value from using Welche's t-test is: ", pval)
s = ("Since our p-value is under the alpha level, \n" 
    "we deem the result to be statistically significant" 
    "and thus we reject the null hypothesis. \n\n"
    "There is a difference in premium price based on surgery history.")
print(s)

"""Diabetes distribution"""

# Power Analysis
effect_size_diabete = effect_size(diabetes_1, diabetes_0)

# Perform power analysis to find sample size for given effect
obj = TTestIndPower()
n = obj.solve_power(effect_size=effect_size_diabete, alpha=alpha, power=power, 
                    ratio=1, alternative='two-sided')
  
print('Sample size/Number needed in each group: {:.3f}'.format(n))
print('Sample size of each group: {:.3f}, {:.3f}'.format(diabetes_1.count(), diabetes_0.count()))

# Plot
plt.subplots(1, 1, figsize=(10,6))
        
plt.hist(diabetes_1.values, alpha=.65, label='diabetes', density=True)
plt.hist(diabetes_0.values, alpha=.5, label='non-diabetes', density=True)

mean1 = diabetes_1.values.mean()
mean0 = diabetes_0.values.mean()

plt.vlines(mean1, 0, 1, color='navy', ls='--', label='Mean premium price for diabetes')
plt.vlines(mean0, 0, 1, color='red', ls='--', label='Mean premium price for non-diabetes')

ci_diabetes = stats.t.interval(1 - alpha, len(diabetes_1) - 1, loc=np.mean(diabetes_1), scale=stats.sem(diabetes_1))
ci_no_diabetes = stats.t.interval(1 - alpha, len(diabetes_0) - 1, loc=np.mean(diabetes_0), scale=stats.sem(diabetes_0))

plt.vlines(ci_diabetes[0], 0, 1, color='yellow', ls='--', label='Confidence Interval 95%')
plt.vlines(ci_diabetes[1], 0, 1, color='yellow', ls='--')

plt.vlines(ci_no_diabetes[0], 0, 1, color='yellow', ls='--')
plt.vlines(ci_no_diabetes[1], 0, 1, color='yellow', ls='--')

plt.xlabel('Premium price')
plt.ylabel('Density')
plt.title('Premium price distribution based on diabete status')
plt.legend()

statistics, pval = stats.ttest_ind(diabetes_1, diabetes_0, equal_var=False)
pval

"""Age distribution"""

# Power Analysis
effect_size_age = effect_size(age_above50, age_below50)

# Perform power analysis to find sample size for given effect
obj = TTestIndPower()
n = obj.solve_power(effect_size=effect_size_age, alpha=alpha, power=power, 
                    ratio=1, alternative='two-sided')
  
print('Sample size/Number needed in each group: {:.3f}'.format(n))
print('Sample size of each group: {:.3f}, {:.3f}'.format(age_above50.count(), age_below50.count()))

plt.subplots(1, 1, figsize=(10,6))
        
plt.hist(age_above50.values, alpha=.65, label='age above 50', density=True)
plt.hist(age_below50.values, alpha=.5, label='age below 50', density=True)

mean1 = age_above50.values.mean()
mean0 = age_below50.values.mean()

plt.vlines(mean1, 0, 1, color='navy', ls='--', label='Mean premium price for age above 50')
plt.vlines(mean0, 0, 1, color='red', ls='--', label='Mean premium price for age below 50')

ci_age_above50 = stats.t.interval(1 - alpha, len(age_above50) - 1, loc=np.mean(age_above50), scale=stats.sem(age_above50))
ci_age_below50 = stats.t.interval(1 - alpha, len(age_below50) - 1, loc=np.mean(age_below50), scale=stats.sem(age_below50))

plt.vlines(ci_age_above50[0], 0, 1, color='yellow', ls='--', label='Confidence Interval 95%')
plt.vlines(ci_age_above50[1], 0, 1, color='yellow', ls='--')

plt.vlines(ci_age_below50[0], 0, 1, color='yellow', ls='--')
plt.vlines(ci_age_below50[1], 0, 1, color='yellow', ls='--')

plt.xlabel('Premium price')
plt.ylabel('Density')
plt.title('Premium price distribution based on age')
plt.legend()

statistics, pval = stats.ttest_ind(age_above50, age_below50, equal_var=False)
pval

"""Chronic disease distribution"""

# Power Analysis
effect_size_chronic = effect_size(chronicDisease_1, chronicDisease_0)

# Perform power analysis to find sample size for given effect
obj = TTestIndPower()
n = obj.solve_power(effect_size=effect_size_chronic, alpha=alpha, power=power, 
                    ratio=1, alternative='two-sided')
  
print('Sample size/Number needed in each group: {:.3f}'.format(n))
print('Sample size of each group: {:.3f}, {:.3f}'.format(chronicDisease_1.count(), chronicDisease_0.count()))

plt.subplots(1, 1, figsize=(10,6))
        
plt.hist(chronicDisease_1.values, alpha=.65, label='has chronic disease', density=True)
plt.hist(chronicDisease_0.values, alpha=.5, label='does not have chronic disease', density=True)

mean1 = chronicDisease_1.values.mean()
mean0 = chronicDisease_0.values.mean()

plt.vlines(mean1, 0, 1, color='navy', ls='--', label='Mean premium price for people with chronic disease')
plt.vlines(mean0, 0, 1, color='red', ls='--', label='Mean premium price for people without chronic disease')

ci_chronicDisease_1 = stats.t.interval(1 - alpha, len(chronicDisease_1) - 1, loc=np.mean(chronicDisease_1), scale=stats.sem(chronicDisease_1))
ci_chronicDisease_0 = stats.t.interval(1 - alpha, len(chronicDisease_0) - 1, loc=np.mean(chronicDisease_0), scale=stats.sem(chronicDisease_0))

plt.vlines(ci_chronicDisease_1[0], 0, 1, color='yellow', ls='--', label='Confidence Interval 95%')
plt.vlines(ci_chronicDisease_1[1], 0, 1, color='yellow', ls='--')

plt.vlines(ci_chronicDisease_0[0], 0, 1, color='yellow', ls='--')
plt.vlines(ci_chronicDisease_0[1], 0, 1, color='yellow', ls='--')

plt.xlabel('Premium price')
plt.ylabel('Density')
plt.title('Premium price distribution based on presence of chronic disease')
plt.legend()

statistics, pval = stats.ttest_ind(chronicDisease_1, chronicDisease_0, equal_var=False)
pval

"""# Part III. Prediction"""

#Reference: https://machinelearninghd.com/ridgecv-regression-python/
#Import Libraries
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, ElasticNet, LinearRegression
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

"""Checking the data, if there is multicollinearity."""

#Checking the data, if there is multicollinearity.
plt.figure(figsize=(15,7))
sns.heatmap(df.corr(),annot=True,cmap='viridis')

from sklearn.metrics import mean_absolute_error,r2_score, mean_squared_error
import random
scale = StandardScaler()
scaled = pd.DataFrame(scale.fit_transform(df))

random = random.seed(15020304) #N-number: 

# x_feature = pd.concat([scaled.iloc[:,0:5],scaled.iloc[:,6:-1]],axis=1) #eliminate height
x_train, x_test, y_train, y_test = train_test_split(scaled.iloc[:,:-1], scaled.iloc[:,-1], train_size=0.8,random_state=random) #all features
# x_train, x_test, y_train, y_test = train_test_split(x_feature, scaled.iloc[:,-1], train_size=0.8,random_state=random)
print(x_train.shape, y_train.shape)

# LassoCV
lasso = LassoCV()
lasso.fit(x_train, y_train)
print(f'Optimal alpha: {lasso.alpha_}')

coef = dict()
for i in range(10):
  coef[df.columns[i]] = lasso.coef_[i]
print(f'coefficeints:\n{coef}')

y_pred = lasso.predict(x_test)

print(f'R^2: {lasso.score(x_test, y_test)}')
r2_lasso= lasso.score(x_test, y_test)
rmse_lasso = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'RMSE: {rmse_lasso}')

print(f'R^2: {lasso.score(x_test, y_test)}')
r2_lasso_2= lasso.score(x_test, y_test)
rmse_lasso_2 = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'RMSE: {rmse_lasso}')

# define evaluation
from sklearn.model_selection import RepeatedKFold
cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=1)

from sklearn.metrics import mean_absolute_error,r2_score, mean_squared_error

#Define Ridge Regression Model
# define model
model = Ridge()
model.fit(x_train,y_train)

#Predicting the Model
y_pred = model.predict(x_test)

#Evaluating the model
coef_ridge = model.coef_
r2_ridge = r2_score(y_test,y_pred)
rmse_ridge = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'R^2:{r2_score(y_test,y_pred)}')
print(f'coefficeints:\n{coef_ridge}')
print(f'RMSE:{rmse_ridge}')

#Find the best parameters through GridsearchCV
#define parameters
param = {
    # 'alpha': [0.0001, 0.001, 0.01, 0.1, 1, 10, 100],
    'alpha':np.arange(0.00001, 20, 0.1),
    'fit_intercept':[True,False],
    # 'normalize':[True,False],
'solver':['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga']
       }

#define model
model = Ridge()

# define search
search = GridSearchCV(model, param, scoring='r2', n_jobs=-1, cv=cv)
# execute search
result = search.fit(x_train, y_train)
# summarize result
print('Best Score: %s' % result.best_score_)
print('Best Hyperparameters: %s' % result.best_params_)

model = Ridge(alpha=result.best_params_['alpha'],fit_intercept = result.best_params_['fit_intercept'], solver = result.best_params_['solver'])
model.fit(x_train,y_train)
y_pred = model.predict(x_test)
coef_ridge = model.coef_
r2_ridge = r2_score(y_test,y_pred)
rmse_ridge = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'R^2:{r2_score(y_test,y_pred)}')
print(f'coefficeints:\n{coef_ridge}')
print(f'RMSE:{rmse_ridge}')

r2_ridge_2 = r2_score(y_test,y_pred)
rmse_ridge_2 = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'R^2:{r2_score(y_test,y_pred)}')
print(f'coefficeints:\n{coef_ridge}')
print(f'RMSE:{np.sqrt(mean_absolute_error(y_test,y_pred))}')

#Elastic Net
model = ElasticNet(alpha=0.1, l1_ratio=0.5)
model.fit(x_train,y_train)
y_pred = model.predict(x_test)
coef_elas = model.coef_
r2_elas = r2_score(y_test,y_pred)
rmse_elas = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'R^2:{r2_elas}')
print(f'coefficeints:\n{coef_elas}')
print(f'RMSE:{rmse_elas}')

from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

parametersGrid = {"max_iter": [1, 5, 10],
                  'alpha':np.arange(0.00001, 20, 0.1),
                      # "alpha": [0.0001, 0.001, 0.01, 0.1, 1, 10, 100],
                      "l1_ratio": np.arange(0.0, 1.0, 0.1)}

grid = GridSearchCV(model, parametersGrid, scoring='r2', cv=10)
grid.fit(x_train, y_train)
grid.best_params_

#Elastic Net
model = ElasticNet(alpha=grid.best_params_['alpha'], l1_ratio=grid.best_params_['l1_ratio'])
model.fit(x_train,y_train)
y_pred = model.predict(x_test)
coef_elas = model.coef_
# r2_elas = r2_score(y_test,y_pred)
# rmse_elas = np.sqrt(mean_absolute_error(y_test,y_pred))
# print(f'R^2:{r2_elas}')
# print(f'coefficeints:\n{coef_elas}')
# print(f'RMSE:{rmse_elas}')


r2_elas_2 = r2_score(y_test,y_pred)
rmse_elas_2 = np.sqrt(mean_absolute_error(y_test,y_pred))
print(f'R^2:{r2_score(y_test,y_pred)}')
print(f'coefficeints:\n{coef_elas}')
print(f'RMSE:{np.sqrt(mean_absolute_error(y_test,y_pred))}')

model_assessment = pd.DataFrame(columns=df.columns[:-1])
model_assessment.loc['Lasso'] = coef
model_assessment.loc['Ridge'] = coef_ridge
model_assessment.loc['ElasticNet'] = coef_elas
model_assessment['R^2'] = [r2_lasso,r2_ridge,r2_elas]
model_assessment['RMSE'] = [rmse_lasso,rmse_ridge,rmse_elas]
model_assessment = model_assessment.round(5)

model_assessment

model_assessment.to_csv('/content/drive/MyDrive/Data/model_assessment.csv')

model_assessment2 = pd.DataFrame(index = ['Lasso', 'Ridge','Elastic Net'])
model_assessment2['R^2'] = [r2_lasso,r2_ridge,r2_elas]
model_assessment2['RMSE'] = [rmse_lasso,rmse_ridge,rmse_elas]
model_assessment2['updated R^2'] = [r2_lasso_2,r2_ridge_2,r2_elas_2]
model_assessment2['updated RMSE'] = [rmse_lasso_2,rmse_ridge_2,rmse_elas_2]
model_assessment2 = model_assessment2.round(4)
model_assessment2

plt.scatter(['Lasso', 'Ridge', 'Elastic Net'], model_assessment2['R^2'], color='blue',label='R^2')
plt.scatter(['Lasso', 'Ridge', 'Elastic Net'], model_assessment2['updated R^2'], color='orange',label='updated R^2')
plt.legend()
plt.xticks(rotation=90)
plt.show()

"""# Part IV. Classification"""

from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score, confusion_matrix, ConfusionMatrixDisplay, precision_recall_curve, auc, roc_curve

s = StandardScaler()
temp = df
s.fit(temp[['Age', 'Height', 'Weight', 'PremiumPrice']])
new = s.transform(temp[['Age', 'Height', 'Weight', 'PremiumPrice']]).T
temp.Age = new[0]
temp.Height = new[1]
temp.Weight = new[2]
temp.PremiumPrice = new[3]

X_col = df.columns.drop('Diabetes')
X = df[X_col]
x_train, x_test, y_train, y_test = train_test_split(X, df.Diabetes, train_size=0.8, random_state=15020304)

## Kaiser Criterion: Consider all principal components with eigen values greater than 1.0
pca = PCA()
pca.fit(X)
eigval = pca.explained_variance_
n = 10
x = np.arange(1,11)
plt.bar(x, eigval, color='navy', alpha=0.6)
plt.hlines(1.0,0,11, color='orange')
plt.xlabel('Principal component')
plt.ylabel('Eigenvalue')
plt.xticks(ticks=x)
plt.text(7,1.1,'Kaiser Criterion Line', color='orange')
plt.show()
print(f'Variance explained by the first 2 PC above is: {sum(pca.explained_variance_ratio_[:2])}')

# Use Silhouette Score to find the optimal k for k-means
opt_pca = PCA(n_components=2)
newX = opt_pca.fit_transform(X)
s = []
for i in range(2,11):
    kmeans = KMeans(n_clusters = i)
    kmeans.fit(newX)
    cID = kmeans.labels_
    s.append(silhouette_score(newX, cID))

plt.plot(np.arange(2,11), s)
plt.xlabel('number of clusters for K-Means')
plt.ylabel('mean silhouette score')
plt.show()

# optimize k-means with clusters of 2
opt_kmeans = KMeans(n_clusters=2)
opt_kmeans.fit(newX)
labels = opt_kmeans.labels_
newX = newX.T

# plot premium by labels

sns.scatterplot(x=newX[0][np.where(labels==0)[0]],y=newX[1][np.where(labels==0)[0]])
sns.scatterplot(x=newX[0][np.where(labels==1)[0]],y=newX[1][np.where(labels==1)[0]])

plt.xlabel('principle component [1]')
plt.ylabel('principle component [2]')
plt.show()

param_grid = {
    "max_depth": [3, 4, 5, 7],
    "learning_rate": [0.1, 0.01, 0.05],
    "gamma": [0, 0.25, 1],
    "reg_lambda": [0, 1, 10],
    "scale_pos_weight": [1, 3, 5],
    "subsample": [0.8],
    "colsample_bytree": [0.5]
}

xgb = XGBClassifier(objective='binary:logistic')
grid = GridSearchCV(xgb, param_grid, scoring='roc_auc')
grid.fit(X, df.Diabetes)

print(grid.best_score_)
print(grid.best_params_)

opt_xgb = XGBClassifier(objective='binary:logistic', **grid.best_params_)
opt_xgb.fit(x_train, y_train)

conf_matrix = confusion_matrix(y_test, opt_xgb.predict(x_test))
dsip = ConfusionMatrixDisplay(confusion_matrix=conf_matrix, display_labels=[0,1])
dsip.plot()
plt.title('Confusion Matrix')
plt.show()

probs = opt_xgb.predict_proba(x_test)[:,1]
fpr, tpr, thresholds = roc_curve(y_test, probs)
random_classifier=np.linspace(0.0, 1.0, 100)
plt.figure(figsize=(6, 4))
plt.plot(fpr, tpr, color="purple")
plt.plot(random_classifier, random_classifier, 'r--')
plt.xlabel("FPR")
plt.ylabel("TPR")
plt.title("ROC Curve")
plt.show()
print(f'feature importance: {opt_xgb.feature_importances_} \nArea under ROC curve: {auc(fpr, tpr)}')