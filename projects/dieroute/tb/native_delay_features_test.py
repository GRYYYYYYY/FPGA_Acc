"""Independent analytic checks of the exploratory multi-output ridge solver."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_native_delay_features import ridge_fit,predict,metrics


class DelayFeaturesTest(unittest.TestCase):
    def test_analytic_ridge_with_constant_feature(self):
        # z is -1,+1. Intercept=3, penalized slope=4/(2+1).
        model=ridge_fit([[0,100],[2,100]],[[1,-2],[5,-10]],1)
        self.assertEqual(model['means'],[1,100])
        self.assertEqual(model['scales'],[1,1])
        for x,expected in ((0,5/3),(1,3),(2,13/3),(4,7)):
            result=predict(model,[x,100])
            self.assertAlmostEqual(result[0],expected)
            self.assertAlmostEqual(result[1],-2*expected)

    def test_correlated_columns_first_order_optimality(self):
        x=[[i,i*i,2*i,17] for i in range(8)];y=[[3*i-2,7-i*i] for i in range(8)]
        penalty=.7;model=ridge_fit(x,y,penalty)
        for k in range(2):
            residuals=[predict(model,row)[k]-target[k] for row,target in zip(x,y)]
            self.assertAlmostEqual(sum(residuals),0,places=8)
            for j in range(4):
                gradient=sum(error*(row[j]-model['means'][j])/model['scales'][j] for row,error in zip(x,residuals))
                gradient+=penalty*model['coefficients'][j+1][k]
                self.assertAlmostEqual(gradient,0,places=8)
        with self.assertRaises(AssertionError):ridge_fit([[float('nan')]],[[1]])

    def test_macro_error_does_not_overweight_fanout(self):
        rows=[dict(net=1,prediction_ps=1,observed_ps=0) for _ in range(9)]+[dict(net=2,prediction_ps=9,observed_ps=0)]
        result=metrics(rows)
        self.assertAlmostEqual(result['mae_ps'],1.8)
        self.assertAlmostEqual(result['net_macro_mae_ps'],5)
        self.assertEqual(result['p95_absolute_error_ps'],9)


if __name__=='__main__':unittest.main()
